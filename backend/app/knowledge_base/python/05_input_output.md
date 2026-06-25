# Python 输入与输出

## 标准输出 print

```python
print("Hello")
print("a", "b", "c", sep="-")     # a-b-c
print("no newline", end=" ")
print("continued")
print(f"value={42}")
```

| 参数 | 默认 | 说明 |
|:---|:---|:---|
| `sep` | 空格 | 多个值之间的分隔符 |
| `end` | `\n` | 结尾字符 |
| `file` | stdout | 可重定向到文件 |

### 重定向输出

```python
with open("log.txt", "w", encoding="utf-8") as f:
    print("写入文件", file=f)
```

## 标准输入 input

```python
name = input("请输入姓名: ")   # 返回 str
age = int(input("请输入年龄: "))  # 需手动转换
```

`input()` 总是返回字符串，数值类型要显式转换。

### 安全读取数值

```python
while True:
    try:
        n = int(input("输入整数: "))
        break
    except ValueError:
        print("无效输入，请重试")
```

## 格式化输出表格

```python
rows = [("Alice", 90), ("Bob", 85)]
print(f"{'Name':<10} {'Score':>5}")
print("-" * 16)
for name, score in rows:
    print(f"{name:<10} {score:>5}")
```

对齐符号：`<` 左对齐，`>` 右对齐，`^` 居中。

## 读写文件基础

```python
# 写
with open("data.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n")
    f.writelines(["第二行\n", "第三行\n"])

# 读
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()       # 整个文件
    # lines = f.readlines()  # 列表
    # for line in f:         # 逐行，大文件推荐
```

`with` 语句自动关闭文件，即使发生异常。

### 文件模式

| 模式 | 含义 |
|:---|:---|
| `r` | 只读（默认） |
| `w` | 写入，覆盖已有 |
| `a` | 追加 |
| `x` | 创建，文件存在则失败 |
| `rb` / `wb` | 二进制读写 |

## JSON 序列化

```python
import json

data = {"name": "Alice", "scores": [90, 85]}
json.dumps(data, ensure_ascii=False)  # 转字符串

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
```

## 命令行参数

```python
import sys

print(sys.argv)   # ['script.py', 'arg1', 'arg2']
```

更规范的方式用 `argparse`：

```python
import argparse

parser = argparse.ArgumentParser(description="示例程序")
parser.add_argument("name", help="用户名")
parser.add_argument("-v", "--verbose", action="store_true")
args = parser.parse_args()
print(args.name, args.verbose)
```

## 学习要点总结

1. `print` 的 `sep`、`end`、`file` 参数灵活控制输出
2. `input()` 返回 str，数值需显式转换
3. 文件操作始终指定 `encoding="utf-8"`，使用 `with` 管理资源
4. JSON 是程序间交换数据的常用格式
5. 命令行程序用 `argparse` 解析参数
