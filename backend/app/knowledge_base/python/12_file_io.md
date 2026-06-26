# Python 文件操作

## pathlib（推荐）

面向对象的路径操作，Python 3.4+：

```python
from pathlib import Path

p = Path("data") / "subdir" / "file.txt"
p.parent           # data/subdir
p.name             # file.txt
p.stem             # file
p.suffix           # .txt

p.exists()
p.is_file()
p.mkdir(parents=True, exist_ok=True)
```

### 读写文本

```python
p = Path("notes.txt")
p.write_text("Hello\nWorld", encoding="utf-8")
content = p.read_text(encoding="utf-8")

lines = p.read_text(encoding="utf-8").splitlines()
```

### 读写二进制

```python
data = Path("image.png").read_bytes()
Path("copy.png").write_bytes(data)
```

### 遍历目录

```python
for f in Path(".").glob("*.py"):
    print(f)

for f in Path(".").rglob("*.md"):   # 递归
    print(f)
```

## 传统 open 方式

```python
with open("log.txt", "a", encoding="utf-8") as f:
    f.write("新日志\n")

with open("log.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.rstrip("\n")
        process(line)
```

大文件**逐行读取**，避免 `read()` 一次载入内存。

## CSV 处理

```python
import csv

with open("data.csv", "r", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["name"], row["score"])

with open("out.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "score"])
    writer.writeheader()
    writer.writerow({"name": "Alice", "score": 90})
```

`newline=""` 防止 Windows 下多余空行。

## 上下文管理器

`with` 保证资源释放：

```python
with open("f.txt") as f:
    data = f.read()
# 自动 close，即使异常
```

自定义上下文管理器：

```python
from contextlib import contextmanager

@contextmanager
def temp_change_dir(path):
    import os
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)
```

## 文件编码

始终显式指定 `encoding="utf-8"`。读取未知编码时可尝试：

```python
text = raw_bytes.decode("utf-8", errors="replace")
```

## 学习要点总结

1. 新项目优先用 `pathlib.Path` 操作路径
2. 文本文件指定 UTF-8 编码
3. 大文件用逐行迭代，不要一次性 read
4. CSV 用 `csv` 模块，注意 `newline=""`
5. `with` 语句自动管理文件关闭
