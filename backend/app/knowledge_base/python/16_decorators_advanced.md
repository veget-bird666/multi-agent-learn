# Python 装饰器与常用进阶

## 函数装饰器

装饰器是**接受函数、返回函数**的高阶函数，用于在不修改原函数代码的情况下增强行为：

```python
import functools
import time

def timer(func):
    @functools.wraps(func)   # 保留原函数名和文档
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} 耗时 {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_task():
    time.sleep(0.1)
    return "done"

slow_task()
```

`@timer` 等价于 `slow_task = timer(slow_task)`。

### 带参数的装饰器

```python
def repeat(n: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello, {name}")
```

## 类装饰器

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0
        functools.update_wrapper(self, func)

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"调用第 {self.count} 次")
        return self.func(*args, **kwargs)

@CountCalls
def say_hi():
    print("Hi")
```

## 类型注解进阶

```python
from typing import Optional, Union, Callable, TypeVar, Generic

T = TypeVar("T")

def first(items: list[T]) -> Optional[T]:
    return items[0] if items else None

def apply(func: Callable[[int], int], x: int) -> int:
    return func(x)

# Python 3.10+ 简写
def parse(s: str) -> int | None:
    ...
```

静态检查工具：`mypy`、`pyright`。

## 正则表达式 re

```python
import re

text = "Contact: alice@example.com or bob@test.org"
re.findall(r"\w+@\w+\.\w+", text)
re.sub(r"\d+", "X", "a1b22c")   # "aXbXc"

match = re.match(r"(\d{4})-(\d{2})-(\d{2})", "2024-06-25")
if match:
    year, month, day = match.groups()
```

| 元字符 | 含义 |
|:---|:---|
| `.` | 任意字符 |
| `\d` | 数字 |
| `\w` | 字母数字下划线 |
| `+` | 一个或多个 |
| `*` | 零个或多个 |
| `?` | 零个或一个 |

## 并发简介

### threading（I/O 密集型）

```python
import threading

def worker(name):
    print(f"Thread {name}")

t = threading.Thread(target=worker, args=("A",))
t.start()
t.join()
```

GIL 限制 CPU 密集型任务的并行，I/O 等待时可切换线程。

### asyncio（异步 I/O）

```python
import asyncio

async def fetch(url: str) -> str:
    await asyncio.sleep(0.1)   # 模拟 I/O
    return f"data from {url}"

async def main():
    results = await asyncio.gather(
        fetch("a.com"),
        fetch("b.com"),
    )
    print(results)

asyncio.run(main())
```

适合高并发网络请求、Web 服务。

## 常用内置函数

```python
map(lambda x: x * 2, [1, 2, 3])
filter(lambda x: x > 0, [-1, 0, 1, 2])
sorted(items, key=lambda x: x["score"], reverse=True)
any([False, True, False])    # True
all([True, True, False])     # False
zip([1, 2], ["a", "b"])
enumerate(["a", "b", "c"])
```

## 学习要点总结

1. 装饰器用 `@` 语法包装函数，常见用途：日志、计时、权限
2. `@functools.wraps` 保留被装饰函数的元信息
3. `typing` 模块增强类型注解，`mypy` 做静态检查
4. `re` 处理文本匹配，`asyncio` 处理高并发 I/O
5. 推导式、生成器、装饰器是 Python 进阶的三大利器
