# Python 列表与元组

## 列表 (list)

有序、**可变**的序列：

```python
nums = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]
empty = []
```

### 常用操作

```python
lst = [1, 2, 3]
lst.append(4)          # [1,2,3,4]
lst.insert(0, 0)       # [0,1,2,3,4]
lst.extend([5, 6])     # 合并
lst.pop()              # 弹出末尾，返回 6
lst.remove(2)          # 删除第一个值为 2 的元素
len(lst)
3 in lst
lst.index(3)
lst.count(3)
lst.sort()             # 原地排序
sorted(lst)            # 返回新列表
lst.reverse()
```

### 切片

```python
a = [0, 1, 2, 3, 4, 5]
a[1:4]      # [1, 2, 3]
a[:3]       # [0, 1, 2]
a[3:]       # [3, 4, 5]
a[::2]      # [0, 2, 4]
a[1:4] = [10, 20]   # 替换切片
```

### 列表推导式

```python
squares = [x ** 2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
matrix = [[i * j for j in range(3)] for i in range(3)]
```

## 元组 (tuple)

有序、**不可变**的序列：

```python
point = (3, 4)
single = (42,)       # 单元素元组必须加逗号
empty = ()
```

### 为何使用元组？

- 不可变 → 可作 dict 的键、set 的元素
- 比列表更省内存
- 表示固定结构（坐标、RGB、数据库行）

### 解包

```python
x, y = (3, 4)
first, *rest = (1, 2, 3, 4)   # first=1, rest=[2,3,4]
a, b = b, a                    # 交换
```

### 命名元组

```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
p.x, p.y
```

## list vs tuple

| 特性 | list | tuple |
|:---|:---|:---|
| 可变性 | 可变 | 不可变 |
| 语法 | `[1, 2]` | `(1, 2)` |
| 性能 | 略慢 | 略快 |
| 用途 | 动态集合 | 固定记录 |

## 浅拷贝陷阱

```python
matrix = [[0] * 3] * 3   # 危险！三行引用同一列表
matrix[0][0] = 1
# matrix 全变成 [1,0,0]

# 正确
matrix = [[0] * 3 for _ in range(3)]
```

## 学习要点总结

1. list 可变，tuple 不可变
2. 列表推导式是 Python 标志性语法
3. 解包和 `*rest` 在函数参数、循环中广泛使用
4. 单元素元组必须写 `(x,)`
5. 避免 `[[]] * n` 式嵌套，用推导式创建二维列表
