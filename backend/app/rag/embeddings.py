"""
嵌入模块 — 支持两种模式：
  1. 讯飞星火 Embedding API（需在控制台激活服务）
  2. 本地轻量嵌入（无需外部依赖，开发/测试用）

自动检测：Spark 服务可用 → 使用 Spark，否则 → 使用本地模式。

用法:
    from app.rag.embeddings import get_embeddings
    embedder = get_embeddings()
    vector = embedder.embed_query("C语言指针是什么")
"""
import json
import base64
import hashlib
import hmac
import re
from datetime import datetime
from enum import Enum
from functools import lru_cache
from time import mktime
from typing import Optional
from urllib.parse import urlencode
from wsgiref.handlers import format_date_time

import numpy as np
import requests

from app.config import settings


# ═══════════════════════════════════════════════════════════
#  模式 A: 讯飞星火 Embedding API
# ═══════════════════════════════════════════════════════════

EMBEDDING_URL = "https://emb-cn-huabei-1.xf-yun.com/"


class SparkEmbeddingError(RuntimeError):
    """星火 Embedding API 调用异常。"""
    pass


def _sign_url(api_key: str, api_secret: str) -> str:
    """生成带鉴权的完整请求 URL（参数拼在 query string 中）。"""
    host = "emb-cn-huabei-1.xf-yun.com"
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))

    signature_origin = f"host: {host}\ndate: {date}\nPOST / HTTP/1.1"
    signature_sha = base64.b64encode(
        hmac.new(api_secret.encode(), signature_origin.encode(), hashlib.sha256).digest()
    ).decode()

    authorization_origin = (
        f'api_key="{api_key}", algorithm="hmac-sha256", '
        f'headers="host date request-line", signature="{signature_sha}"'
    )
    authorization = base64.b64encode(authorization_origin.encode()).decode()

    return f"https://{host}/?{urlencode({'host': host, 'date': date, 'authorization': authorization})}"


class SparkEmbeddings:
    """讯飞星火 Embedding API 封装，返回 2560 维 float32 向量。"""

    _last_request_time: float = 0.0  # 类级限流

    def __init__(self, app_id=None, api_key=None, api_secret=None, timeout=60, min_interval=1.0):
        self.app_id = app_id or settings.SPARK_APP_ID
        self.api_key = api_key or settings.SPARK_API_KEY
        self.api_secret = api_secret or settings.SPARK_API_SECRET
        self.timeout = timeout
        self._min_interval = min_interval

    def _throttle(self):
        """请求间隔控制（类级）。"""
        import time
        elapsed = time.time() - SparkEmbeddings._last_request_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        SparkEmbeddings._last_request_time = time.time()

    def _request(self, text: str, domain: str) -> list[float]:
        self._throttle()
        url = _sign_url(self.api_key, self.api_secret)
        messages = {"messages": [{"content": text, "role": "user"}]}
        body = {
            "header": {"app_id": self.app_id, "uid": "39769795890", "status": 3},
            "parameter": {"emb": {"domain": domain, "feature": {"encoding": "utf8"}}},
            "payload": {
                "messages": {
                    "text": base64.b64encode(
                        json.dumps(messages, ensure_ascii=False).encode()
                    ).decode(),
                }
            },
        }
        resp = requests.post(url, json=body, headers={"Content-Type": "application/json"},
                             timeout=self.timeout)
        try:
            result = resp.json()
        except json.JSONDecodeError:
            resp.raise_for_status()
            raise

        code = result.get("header", {}).get("code", -1)
        if code == 11200:
            raise SparkEmbeddingError("SERVICE_NOT_ACTIVATED: Embedding 服务未开通")
        if code != 0:
            raise SparkEmbeddingError(
                f"API 错误 (code={code}): {result.get('header', {}).get('message', '')}"
            )
        text_base = result["payload"]["feature"]["text"]
        dt = np.dtype(np.float32).newbyteorder("<")
        return np.frombuffer(base64.b64decode(text_base), dtype=dt).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._request(text, domain="query")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """对文档列表进行向量化（domain=para）。"""
        return [self._request(t, domain="para") for t in texts]


# ═══════════════════════════════════════════════════════════
#  模式 B: 本地轻量嵌入（开发兜底）
# ═══════════════════════════════════════════════════════════

_LOCAL_DIM = 256


class LocalEmbeddings:
    """
    本地轻量嵌入，基于 hash 的 TF 向量 + L2 归一化。

    特点:
      - 无外部依赖 (只需 numpy)
      - 确定性输出（同文本 → 同向量）
      - 256 维，可用余弦相似度比较
      - **不适合生产**，仅用于开发/测试管道
    """

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    @staticmethod
    def _embed(text: str) -> list[float]:
        tokens = re.findall(r"\w+", text.lower())
        vec = np.zeros(_LOCAL_DIM, dtype=np.float32)
        for token in set(tokens):
            h = int(hashlib.md5(token.encode()).hexdigest(), 16)
            vec[h % _LOCAL_DIM] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec /= norm
        return vec.tolist()


# ═══════════════════════════════════════════════════════════
#  工厂函数 — 自动选择模式
# ═══════════════════════════════════════════════════════════

class EmbeddingMode(str, Enum):
    SPARK = "spark"      # 讯飞星云 Embedding API
    LOCAL = "local"      # 本地轻量兜底
    AUTO = "auto"        # 自动检测


def _probe_spark() -> bool:
    """快速检测 Spark Embedding 服务是否可用。"""
    try:
        emb = SparkEmbeddings()
        emb._request("test", domain="query")
        return True
    except SparkEmbeddingError as e:
        if "SERVICE_NOT_ACTIVATED" in str(e):
            print("[Embedding]  Spark Embedding 未开通，切换到本地模式")
        return False
    except Exception as e:
        print(f"[Embedding]  Spark Embedding 不可用 ({e})，切换到本地模式")
        return False


@lru_cache(maxsize=1)
def get_embeddings():
    """
    获取 Embedding 实例（单例）。

    模式选择:
      - AUTO / SPARK: 先尝试 Spark API，失败则降级到本地
      - LOCAL: 直接使用本地嵌入（最快，无网络开销）
    """
    mode = getattr(settings, "EMBEDDING_MODE", "auto")
    if mode == EmbeddingMode.LOCAL:
        print("[Embedding]  使用本地嵌入模式")
        return LocalEmbeddings()
    if mode == EmbeddingMode.SPARK or (mode == EmbeddingMode.AUTO and _probe_spark()):
        print("[Embedding]  使用讯飞星火 Embedding API")
        try:
            return SparkEmbeddings()
        except Exception:
            pass
    # 兜底：本地模式
    print("[Embedding]  使用本地嵌入模式（兜底）")
    return LocalEmbeddings()
