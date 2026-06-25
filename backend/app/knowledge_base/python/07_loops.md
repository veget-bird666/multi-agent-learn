# Python 循环

## while 循环

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

条件为 False 时退出。注意避免无限循环。

## for 循环

Python 的 `for` 是**迭代器循环**，不是 C 风格的计数循环：

```python
for fruit in ["apple", "banana", "cherry"]:
    print(fruit)

for char in "Python":
    print(char)

for key, value in {"a": 1, "b": 2}.items():
    print(key, value)
```

## range 函数

生成整数序列，常用于计数：

```python
range(5)           # 0, 1, 2, 3, 4
range(2, 8)        # 2, 3, 4, 5, 6, 7
range(0, 10, 2)    # 0, 2, 4, 6, 8
list(range(3))     # [0, 1, 2]
```

```python
for i in range(len(items)):   # 需要索引时
    print(i, items[i])

for i, item in enumerate(items):  # 更 Pythonic
    print(i, item)
```

## break 与 continue

```python
for n in range(10):
    if n == 3:
        continue    # 跳过本次，进入下一次
    if n == 7:
        break       # 跳出整个循环
    print(n)
```

## else 子句

循环的 `else` 在**正常结束**（未 break）时执行：

```python
for n in range(2, 10):
    if n % 7 == 0:
        print("找到因子")
        break
else:
    print("没有因子")   # 未 break 时执行
```

常用于搜索：找到则 break，否则 else 报告未找到。

## 嵌套循环

```python
for i in range(3):
    for j in range(3):
        print(f"({i},{j})", end=" ")
    print()
```

打印乘法表、矩阵遍历等场景常用。

## 循环性能提示

```python
# 慢：每次循环创建新列表
result = []
for i in range(1000000):
    result.append(i * 2)

# 快：列表推导式
result = [i * 2 for i in range(1000000)]
```

大循环中避免重复计算、避免在循环内做 I/O。

## zip 并行迭代

```python
names = ["Alice", "Bob"]
scores = [90, 85]
for name, score in zip(names, scores):
    print(name, score)
```

## 学习要点总结

1. `for` 遍历可迭代对象，不限于 range
2. `enumerate` 同时获取索引和值，`zip` 并行遍历多个序列
3. `break` 跳出循环，`continue` 跳过当前迭代
4. 循环的 `else` 在未 break 时执行，适合搜索模式
5. 简单变换优先用列表推导式，可读且更快
