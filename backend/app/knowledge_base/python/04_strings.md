# Python 字符串

## 字符串基础

字符串是**不可变**的 Unicode 字符序列：

```python
s1 = "hello"
s2 = 'world'
s3 = """多行
字符串"""
s4 = r"C:\new\file"   # 原始字符串，不转义 \n
```

## 索引与切片

```python
s = "Python"
s[0]      # 'P'
s[-1]     # 'n'  负索引从末尾数
s[0:3]    # 'Pyt'
s[::2]    # 'Pto'  步长 2
s[::-1]   # 'nohtyP'  反转
```

切片 `[start:stop:step]`：**左闭右开**，不修改原字符串。

## 常用方法

| 方法 | 作用 |
|:---|:---|
| `s.upper()` / `s.lower()` | 大小写转换 |
| `s.strip()` | 去除首尾空白 |
| `s.split(",")` | 分割为列表 |
| `",".join(lst)` | 列表拼接为字符串 |
| `s.replace("a", "b")` | 替换 |
| `s.find("sub")` | 查找子串，未找到返回 -1 |
| `s.startswith("pre")` | 前缀判断 |
| `s.isdigit()` | 是否全为数字 |

```python
"  hello  ".strip()           # "hello"
"a,b,c".split(",")           # ["a", "b", "c"]
"-".join(["2024", "06", "25"])  # "2024-06-25"
```

## 字符串格式化

### f-string（推荐，Python 3.6+）

```python
name = "Alice"
age = 20
f"Name: {name}, Age: {age}"
f"{3.14159:.2f}"      # "3.14"
f"{1000000:,}"        # "1,000,000"
f"{name=}"            # "name='Alice'"  调试写法
```

### format 方法

```python
"{} is {} years old".format(name, age)
"{0} {1}".format("Hello", "World")
"{name}".format(name="Bob")
```

### % 格式化（旧式）

```python
"%s is %d years old" % (name, age)
```

新项目优先 f-string。

## 字符串与编码

```python
s = "中文"
s.encode("utf-8")                    # bytes
b"hello".decode("utf-8")             # str
```

| 概念 | 说明 |
|:---|:---|
| `str` | Unicode 文本 |
| `bytes` | 原始字节序列 |
| 编码 | str → bytes（如 UTF-8） |
| 解码 | bytes → str |

读写文件、网络传输时必须正确处理编码。

## 字符串不可变的影响

```python
result = ""
for c in "abc":
    result += c   # 每次创建新对象，低效

# 推荐
"".join(["a", "b", "c"])
```

大量拼接用 `join` 或 `io.StringIO`。

## 学习要点总结

1. 字符串不可变，切片和方法是返回新对象
2. 负索引 `-1` 表示最后一个字符
3. f-string 是首选格式化方式
4. 区分 `str`（文本）和 `bytes`（字节）
5. 大量拼接用 `join`，避免循环 `+=`
