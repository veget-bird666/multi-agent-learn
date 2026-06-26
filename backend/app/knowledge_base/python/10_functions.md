# Python 函数

## 定义与调用

```python
def greet(name: str) -> str:
    """返回问候语。"""
    return f"Hello, {name}!"

result = greet("Alice")
```

- 函数是一等公民，可赋值、传参、返回
- 类型注解可选，帮助阅读和静态检查

## 参数类型

### 位置参数与关键字参数

```python
def describe(name, age, city="Beijing"):
    return f"{name}, {age}, {city}"

describe("Alice", 20)
describe("Bob", 25, city="Shanghai")
describe(age=30, name="Carol", city="Guangzhou")
```

### *args 与 **kwargs

```python
def log(*args, **kwargs):
    print("args:", args)       # 元组
    print("kwargs:", kwargs)   # 字典

log(1, 2, 3, level="INFO", module="main")
```

### 仅限关键字参数（Python 3+）

```python
def connect(host, *, port=8080, timeout=30):
    pass

connect("localhost", port=9000)   # port 必须关键字传递
```

## 返回值

```python
def min_max(nums):
    return min(nums), max(nums)   # 返回元组

lo, hi = min_max([3, 1, 4, 1, 5])
```

无 `return` 或 `return`  alone → 返回 `None`。

## 作用域与 LEGB

查找顺序：**L**ocal → **E**nclosing → **G**lobal → **B**uilt-in

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)
    inner()

outer()   # local
print(x)  # global
```

修改外层变量用 `nonlocal`，修改全局用 `global`（尽量少用）。

## 可变默认参数陷阱

```python
# 错误！
def append_item(item, lst=[]):
    lst.append(item)
    return lst

append_item(1)   # [1]
append_item(2)   # [1, 2]  不是 [2]！

# 正确
def append_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

默认值在**函数定义时**只求值一次。

## lambda 表达式

```python
square = lambda x: x ** 2
sorted(items, key=lambda x: x["score"], reverse=True)
```

仅适合单行简单逻辑，复杂逻辑用 `def`。

## 文档字符串 docstring

```python
def add(a: int, b: int) -> int:
    """两数之和。

    Args:
        a: 第一个加数
        b: 第二个加数

    Returns:
        和
    """
    return a + b

help(add)
```

## 学习要点总结

1. 函数支持位置、关键字、默认、*args、**kwargs 多种参数形式
2. LEGB 规则解释变量查找顺序
3. 永远不要用可变对象作默认参数
4. lambda 适合简单 key 函数，复杂逻辑用 def
5. 写 docstring 和类型注解提升可维护性
