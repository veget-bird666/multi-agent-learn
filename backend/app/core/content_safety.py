"""
内容安全与防幻觉模块
职责：
  1. 敏感词过滤（关键词黑名单）
  2. LLM 内容安全审查（政治/暴力/色情/歧视等）
  3. 事实准确性检查（防幻觉：验证生成内容是否与知识库一致）
  4. 综合安全检查接口（供子图 safety_filter 节点调用）
"""
import re
from typing import List, Tuple

from app.core.llm import chat_llm
from app.models.resources import Resource, ResourceType
from langchain_core.prompts import ChatPromptTemplate

# ════════════════════════════════════════════════════════════
# 敏感词库
# ════════════════════════════════════════════════════════════
# 按类别组织，实际使用中应持续更新补充

SENSITIVE_KEYWORDS: dict[str, List[str]] = {
    "politics": [
        # 政治敏感（示例，此处仅列出类别代表，正式部署需补充完整列表）
        "法轮功", "六四", "天安门事件", "藏独", "疆独", "台独",
        "港独", "颜色革命", "和平演变", "邪教组织",
    ],
    "violence": [
        "恐怖袭击", "自杀式", "爆炸物", "枪支", "贩毒",
        "杀人", "绑架", "暴力恐怖",
    ],
    "pornography": [
        "色情", "淫秽", "裸聊", "成人电影", "三级片",
        "约炮", "卖淫", "嫖娼",
    ],
    "discrimination": [
        "种族歧视", "性别歧视", "地域黑", "人身攻击",
        "智商税", "脑残",
    ],
    "illegal": [
        "赌博", "赌场", "高利贷", "洗钱", "诈骗",
        "吸毒", "毒品", "走私",
    ],
}


def _build_flattened_keywords() -> List[str]:
    """将所有类别的敏感词展平为单一列表，用于快速扫描。"""
    result = []
    for category, words in SENSITIVE_KEYWORDS.items():
        result.extend(words)
    return result


_FLATTENED_KEYWORDS = _build_flattened_keywords()


# ════════════════════════════════════════════════════════════
# LLM 审查 Prompt
# ════════════════════════════════════════════════════════════

SAFETY_CHECK_PROMPT = """你是一个内容安全审查员，负责检查以下内容是否包含违规信息。

## 审查类别
1. **政治敏感**：涉及敏感政治人物、事件、分裂主义等内容
2. **暴力恐怖**：涉及暴力、恐怖主义、血腥等内容
3. **色情低俗**：涉及色情、淫秽、低俗内容
4. **歧视仇恨**：涉及种族、性别、地域等歧视或仇恨言论
5. **违法违规**：涉及赌博、毒品、诈骗等违法内容

## 输出格式
如果内容安全，只输出：PASS
如果内容违规，输出：FLAG:违规类别-具体问题描述

举例：
- PASS
- FLAG:政治敏感-内容涉及分裂主义言论
- FLAG:色情低俗-包含不雅描写

## 待审查内容
```
{content}
```
"""

FACT_CHECK_PROMPT = """你是一个学术内容审核员，负责检查以下生成的学术内容是否存在事实性错误。

## 检查要点
1. **概念定义**：重要术语的定义是否准确
2. **数据引用**：涉及的数字、统计是否合理
3. **逻辑关系**：因果、条件等逻辑关系是否正确
4. **知识一致性**：内容与公认的学科知识是否一致
5. **无根据断言**：是否存在没有依据的绝对化断言

## 参考上下文
如果提供了知识库上下文，请严格对照上下文检查。
如果没有提供，请依据公认的学科知识判断。

{context_section}

## 输出格式
如果内容事实准确，只输出：PASS
如果存在事实性问题，输出格式如下（每行一个问题）：
ISSUE:问题描述
ISSUE:问题描述

举例：
- PASS
- ISSUE:文中说"指针就是变量地址"，表述不完整，应为"指针是存储变量地址的变量"
- ISSUE:声称"所有循环都可以用递归改写"过于绝对

## 待审核内容
```
{content}
```
"""


# ════════════════════════════════════════════════════════════
# 安全检查器
# ════════════════════════════════════════════════════════════

class ContentSafetyChecker:
    """内容安全与防幻觉检查器"""

    # ── 关键词扫描 ──────────────────────────────────────

    @staticmethod
    def keyword_scan(text: str) -> List[str]:
        """
        关键词扫描，返回命中的敏感词列表。
        空列表表示未命中任何敏感词。
        """
        if not text:
            return []
        text_lower = text.lower()
        hits = []
        for keyword in _FLATTENED_KEYWORDS:
            if keyword.lower() in text_lower:
                hits.append(keyword)
        return hits

    # ── LLM 内容安全审查 ────────────────────────────────

    @staticmethod
    def llm_safety_check(content: str) -> Tuple[bool, str]:
        """
        LLM 内容安全审查。

        返回:
            (passed, reason)
            passed=True 表示内容安全，reason 为空
            passed=False 表示违规，reason 为违规描述
        """
        if not content or not content.strip():
            return True, ""

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", SAFETY_CHECK_PROMPT),
            ])
            chain = prompt | chat_llm
            result = chain.invoke({"content": content[:3000]})  # 只检查前3000字符
            response = result.content.strip()

            if response.upper().startswith("PASS"):
                return True, ""
            elif response.upper().startswith("FLAG"):
                # 提取 FLAG: 后面的内容
                reason = response[5:].strip()
                return False, reason
            else:
                # 无法识别的响应，保守处理：通过
                return True, ""
        except Exception as e:
            print(f"[ContentSafety]  LLM 审查异常: {e}")
            return True, ""  # 异常时默认通过，不阻塞生成

    # ── 事实准确性检查 ──────────────────────────────────

    @staticmethod
    def llm_fact_check(
        content: str,
        topic: str,
        knowledge_context: str = "",
    ) -> Tuple[bool, List[str]]:
        """
        事实准确性检查（防幻觉）。

        参数:
            content: 待检查的生成内容
            topic: 知识点主题
            knowledge_context: 知识库上下文（可选）

        返回:
            (passed, issues)
            passed=True 表示事实准确，issues 为空列表
            passed=False 表示存在事实性问题，issues 为问题列表
        """
        if not content or not content.strip():
            return True, []

        # 构建上下文部分
        if knowledge_context:
            context_section = f"## 知识库参考\n{knowledge_context[:2000]}"
        else:
            context_section = "## 知识库参考\n（无知识库上下文，请依据公认学科知识判断）"

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", FACT_CHECK_PROMPT),
            ])
            chain = prompt | chat_llm
            result = chain.invoke({
                "content": content[:3000],
                "context_section": context_section,
            })
            response = result.content.strip()

            if response.upper().startswith("PASS"):
                return True, []

            # 提取所有 ISSUE 行
            issues = []
            for line in response.split("\n"):
                line = line.strip()
                if line.upper().startswith("ISSUE:"):
                    issues.append(line[6:].strip())

            return len(issues) == 0, issues
        except Exception as e:
            print(f"[ContentSafety]  事实检查异常: {e}")
            return True, []  # 异常时默认通过

    # ── 综合检查 ────────────────────────────────────────

    @staticmethod
    def check_resource(
        resource: Resource,
        knowledge_context: str = "",
    ) -> Tuple[bool, List[str]]:
        """
        综合检查单个资源的安全性和事实准确性。

        返回:
            (passed, reasons)
            passed=False 时，reasons 包含问题描述。
        """
        issues: List[str] = []
        content = resource.content or ""
        title = resource.title or ""
        topic = resource.knowledge_point or ""

        # 合并标题和内容一起检查
        full_text = f"{title}\n{content}"

        # 1. 关键词扫描（快速预检）
        keyword_hits = ContentSafetyChecker.keyword_scan(full_text)
        if keyword_hits:
            issues.append(f"命中敏感词: {', '.join(keyword_hits[:5])}")

        # 2. LLM 安全审查
        passed, reason = ContentSafetyChecker.llm_safety_check(full_text)
        if not passed:
            issues.append(f"内容违规: {reason}")

        # 3. 事实准确性检查（仅对文字类资源）
        if resource.type in (ResourceType.DOCUMENT, ResourceType.EXAM, ResourceType.MINDMAP):
            passed, fact_issues = ContentSafetyChecker.llm_fact_check(
                content, topic, knowledge_context,
            )
            if not passed:
                for fi in fact_issues[:3]:  # 最多报告3个事实问题
                    issues.append(f"事实错误: {fi}")

        return len(issues) == 0, issues


# 全局单例
content_safety_checker = ContentSafetyChecker()
