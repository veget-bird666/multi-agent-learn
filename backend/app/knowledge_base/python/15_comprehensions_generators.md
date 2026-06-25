# Python 推导式与生成器

## 列表推导式

```python
[x ** 2 for x in range(10)]
[x for x in range(20) if x % 2 == 0]
[str(n) for n in range(5) if n != 2]
```

嵌套：

```python
matrix = [[i * j for j in range(3)] for i in range(3)]
flat = [x for row in matrix for x in row]
```

## 字典与集合推导式

```python
{x: x ** 2 for x in range(5)}
{word: len(word) for word in ["hi", "hello"]}
{x for x in range(10) if x % 2 == 0}
```

## 生成器表达式

语法类似列表推导，但用**圆括号**，惰性求值：

```python
gen = (x ** 2 for x in range(1000000))  # 不占大量内存
next(gen)   # 0
next(gen)   # 1

sum(x ** 2 for x in range(100))   # 直接传给函数
```

| 对比 | 列表推导 | 生成器表达式 |
|:---|:---|:---|
| 语法 | `[...]` | `(...)` |
| 内存 | 一次生成全部 | 按需生成 |
| 复用 | 可多次遍历 | 耗尽后需重建 |

## 生成器函数

含 `yield` 的函数返回生成器：

```python
def countdown(n: int):
    while n > 0:
        yield n
        n -= 1

for i in countdown(5):
    print(i)   # 5, 4, 3, 2, 1

gen = countdown(3)
next(gen)   # 3
next(gen)   # 2
```

`yield` 暂停函数，保留局部状态；`next()` 恢复执行到下一个 `yield`。

### 无限序列

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

from itertools import islice
list(islice(fibonacci(), 10))
```

## yield from

委托子生成器：

```python
def chain(*iterables):
    for it in iterables:
        yield from it

list(chain([1, 2], [3, 4]))   # [1, 2, 3, 4]
```

## itertools 常用工具

```python
from itertools import count, cycle, repeat, chain, islice, groupby

list(islice(count(10), 5))        # [10, 11, 12, 13, 14]
list(islice(cycle("AB"), 5))      # ['A','B','A','B','A']

data = [("a", 1), ("a", 2), ("b", 3)]
for key, group in groupby(data, key=lambda x: x[0]):
    print(key, list(group))
```

## 何时用哪种？

| 场景 | 选择 |
|:---|:---|
| 需要完整列表、多次遍历 | 列表推导 |
| 大数据、单次遍历 | 生成器表达式 / 生成器函数 |
| 无限或流式数据 | 生成器函数 |
| 管道式数据处理 | `yield from` + itertools |

## 学习要点总结

1. 推导式简洁创建 list/dict/set
2. 生成器惰性求值，节省内存
3. `yield` 使函数变为可暂停的生成器
4. 大数据或无限序列优先用生成器
5. `itertools` 提供丰富的迭代工具
