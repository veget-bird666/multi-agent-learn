# 学习资源管理工具

上传本地文件到 **阿里云 OSS**，附带资源类型、描述、关键词等元数据，供 RAG 检索使用。

## 快速开始

```bash
cd asset-manager

# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置阿里云 OSS
cp .env.example .env
# 编辑 .env，填入你的 OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET

# 3. 启动
python server.py
```

打开 http://localhost:8001

## 获取阿里云 OSS 配置

1. 登录 https://oss.console.aliyun.com
2. 创建 Bucket：
   - **地域**：选离你近的（如 广州 = oss-cn-guangzhou.aliyuncs.com）
   - **读写权限**：选**"公共读"**（这样才能生成公网可访问的链接）
   - 创建后 Bucket 概览页能看到 **Endpoint**
3. 在 https://ram.console.aliyun.com/manage/ak 获取 AccessKey ID / Secret

## OSS 公网地址格式

配置正确后，上传的文件可通过以下地址访问：

```
https://<bucket>.<endpoint>/<key>
```

示例：`https://my-learning-bucket.oss-cn-guangzhou.aliyuncs.com/images/C/abc123.png`

## 资源目录结构

上传到 OSS 后按类型 + 学科自动组织：

```
images/
  C语言/
    abc123.png
  Python/
    def456.jpg
videos/
  C语言/
    ghi789.mp4
ppt/
documents/
mindmaps/
exams/
code/
```

## 元数据文件

本地 `data/resources.json` 记录所有已上传资源的元数据，格式如下：

```json
{
  "id": "abc123def456",
  "oss_key": "images/C语言/abc123def456.png",
  "url": "https://...",
  "oss_uploaded": true,
  "filename": "指针示意图.png",
  "file_size": 102400,
  "resource_type": "image",
  "title": "C语言指针内存布局",
  "description": "指针变量存储地址的示意图",
  "keywords": ["指针", "内存", "地址"],
  "subject": "C语言",
  "created_at": "2026-06-25T15:00:00"
}
```

## 集成到主项目

在 RAG 检索时通过类型 + 关键词匹配来查找已上传的资源：

```python
store.search("指针内存", where={"type": "image", "subject": "c_programming"})
```
