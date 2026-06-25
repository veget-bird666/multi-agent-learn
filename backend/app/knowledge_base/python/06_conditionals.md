# Python 条件语句

## if / elif / else

```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 60:
    grade = "C"
else:
    grade = "F"
```

**缩进决定代码块**——通常 4 个空格，同一层级必须一致。

## 真值测试

以下值在布尔上下文中为 **False**：

```python
bool(None)    # False
bool(False)
bool(0)
bool(0.0)
bool("")
bool([])
bool({})
bool(set())
```

其余为 True，包括非零数字、非空容器。

### 简写条件

```python
name = ""
display = name or "Anonymous"   # 空则用默认值

if items:          # 非空列表
    process(items)

if not found:      # 更清晰 than == False
    search_again()
```

## 三元表达式

```python
status = "adult" if age >= 18 else "minor"
max_val = a if a > b else b
```

## match-case（Python 3.10+）

结构化模式匹配，类似 switch：

```python
def handle_command(cmd: str) -> str:
    match cmd.split():
        case ["quit"]:
            return "再见"
        case ["load", filename]:
            return f"加载 {filename}"
        case ["save", filename, "as", new_name]:
            return f"另存为 {new_name}"
        case _:
            return "未知命令"
```

支持解构、类型匹配：

```python
match point:
    case (0, 0):
        print("原点")
    case (x, 0) | (0, y):
        print("在轴上")
    case (x, y):
        print(f"点 ({x}, {y})")
```

## 比较与链式

```python
if 0 <= x <= 100:
    print("有效分数")

if a == b == c:
    print("三者相等")
```

## 常见陷阱

### 1. 浮点比较

```python
# 错误
if 0.1 + 0.2 == 0.3:

# 正确
import math
if math.isclose(0.1 + 0.2, 0.3):
```

### 2. is vs ==

```python
if x is None:      # 正确
if x == None:      # 不推荐
```

### 3. 可变默认参数（见函数章节）

条件分支里修改列表默认值会导致意外共享。

## 学习要点总结

1. Python 用缩进表示代码块，不用花括号
2. 空容器、0、None、空字符串均为 False
3. 三元表达式 `a if cond else b` 简洁替代简单 if-else
4. Python 3.10+ 可用 match-case 做结构化分支
5. 浮点比较用 `math.isclose`，None 判断用 `is None`
