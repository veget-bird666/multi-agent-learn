"""
OSS 上传诊断脚本 — 检查二进制文件上传是否完好
用法: python test_oss.py

注意事项：
  1. endpoint 建议用 https:// 开头，防止透明代理篡改二进制数据
  2. 设置 proxies={'http': '', 'https': ''} 禁用系统代理
     （Windows 上 127.0.0.1:18081 等透明代理会篡改二进制文件）
  3. enable_crc=False：Python 3.13 crcmod 兼容性问题
"""
import os
import hashlib
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
import oss2

load_dotenv()

OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID", "")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET", "")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "https://oss-cn-beijing.aliyuncs.com")
OSS_BUCKET = os.getenv("OSS_BUCKET", "")

auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(
    auth, OSS_ENDPOINT, OSS_BUCKET,
    enable_crc=False,
    proxies={'http': '', 'https': ''},
)


def _put_bytes(key: str, data: bytes, content_type: str = "application/octet-stream"):
    """安全上传二进制数据：必须显式传 Content-Length 避免损坏。"""
    return bucket.put_object(
        key=key,
        data=BytesIO(data),
        headers={
            "Content-Type": content_type,
            "Content-Length": str(len(data)),
        },
    )


# ── 测试 1: 上传一段已知的二进制数据 ──
print("=" * 50)
print("测试 1: 上传已知二进制数据")
print("=" * 50)

test_data = b"hello world, this is a test binary file \x00\x01\x02\xff\xfe"
test_key = "_test_binary_upload.bin"

result = _put_bytes(test_key, test_data)
print(f"  上传状态: {result.status}")
print(f"  ETag: {result.etag}")

# 下载回来对比
downloaded = bucket.get_object(test_key).read()
print(f"  原始大小: {len(test_data)} bytes")
print(f"  下载大小: {len(downloaded)} bytes")
print(f"  内容一致: {test_data == downloaded}")

if test_data != downloaded:
    print("  ❌ 基本二进制上传就出问题了！")
else:
    print("  ✅ 基本二进制上传完好")

# 清理
bucket.delete_object(test_key)


# ── 测试 2: BytesIO + Content-Length 上传 ──
print()
print("=" * 50)
print("测试 2: BytesIO + Content-Length 上传")
print("=" * 50)

test_data2 = b"another test with binary \xAB\xCD\xEF" * 1000
test_key2 = "_test_bytesio_upload.bin"

result = _put_bytes(test_key2, test_data2)
print(f"  上传状态: {result.status}")

downloaded2 = bucket.get_object(test_key2).read()
print(f"  原始大小: {len(test_data2)} bytes")
print(f"  下载大小: {len(downloaded2)} bytes")
print(f"  大小一致: {len(test_data2) == len(downloaded2)}")
print(f"  内容一致: {test_data2 == downloaded2}")

bucket.delete_object(test_key2)


# ── 测试 3: 从本地文件上传（模拟视频上传） ──
print()
print("=" * 50)
print("测试 3: 本地文件上传并校验")
print("=" * 50)

# 找 D:/videos 下的第一个视频文件
video_dir = Path("D:/videos")
video_files = list(video_dir.glob("*")) if video_dir.exists() else []

if video_files:
    video_path = video_files[0]
    file_size = video_path.stat().st_size
    print(f"  文件: {video_path.name}")
    print(f"  大小: {file_size / 1024 / 1024:.2f} MB")

    # 计算本地 MD5
    local_md5 = hashlib.md5()
    with open(video_path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            local_md5.update(chunk)
    print(f"  本地 MD5: {local_md5.hexdigest()}")

    # 上传到 OSS（用安全方式）
    remote_key = f"_test_upload/{video_path.name}"
    with open(video_path, "rb") as f:
        content = f.read()
    result = _put_bytes(remote_key, content)
    print(f"  上传状态: {result.status}")

    # 获取 OSS 端的文件信息
    head = bucket.head_object(remote_key)
    oss_size = head.content_length
    oss_md5_raw = head.etag.strip('"')
    print(f"  OSS 大小: {oss_size} bytes")
    print(f"  OSS ETag: {oss_md5_raw}")

    # 下载回来对比
    oss_content = bucket.get_object(remote_key).read()
    oss_md5 = hashlib.md5(oss_content).hexdigest()
    print(f"  下载后 MD5: {oss_md5}")
    print(f"  大小一致: {file_size == len(oss_content)}")
    print(f"  MD5 一致: {local_md5.hexdigest() == oss_md5}")

    if file_size != len(oss_content):
        print(f"  ❌ 大小不匹配! 差异: {file_size - len(oss_content)} bytes")
    elif local_md5.hexdigest() != oss_md5:
        print(f"  ❌ MD5 不匹配! 文件损坏")
    else:
        print(f"  ✅ 文件上传完好无损")

    # 清理
    bucket.delete_object(remote_key)
else:
    print("  D:/videos/ 下没有文件，跳过")

print()
print("=" * 50)
print("诊断完成")
print("=" * 50)
