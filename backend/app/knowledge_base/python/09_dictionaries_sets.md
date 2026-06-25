# Python 字典与集合

## 字典 (dict)

键值对映射，键必须**可哈希**（不可变类型）：

```python
student = {
    "name": "Alice",
    "age": 20,
    "scores": [90, 85, 88]
}

student["name"]           # "Alice"
student.get("phone", "N/A")  # 不存在返回默认值
student["grade"] = "A"    # 添加/修改
del student["age"]
"name" in student         # True
```

### 常用方法

```python
d = {"a": 1, "b": 2, "c": 3}
d.keys()
d.values()
d.items()       # dict_items，用于 for 循环

for key, value in d.items():
    print(key, value)

d.update({"b": 20, "d": 4})
d.pop("a")
d.popitem()     # 弹出最后一项（Python 3.7+ 有序）
```

### Python 3.7+ 有序

字典保持**插入顺序**，可当作有序映射使用。

### 字典推导式

```python
squares = {x: x ** 2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

word_count = {}
for word in words:
    word_count[word] = word_count.get(word, 0) + 1
```

### defaultdict 与 Counter

```python
from collections import defaultdict, Counter

dd = defaultdict(list)
dd["fruits"].append("apple")

Counter("abracadabra")   # Counter({'a': 5, 'b': 2, ...})
```

## 集合 (set)

无序、**不重复**的可变集合：

```python
s = {1, 2, 3, 3, 2}   # {1, 2, 3}
s.add(4)
s.remove(2)
s.discard(99)         # 不存在不报错

a = {1, 2, 3}
b = {2, 3, 4}
a | b     # 并集 {1,2,3,4}
a & b     # 交集 {2, 3}
a - b     # 差集 {1}
a ^ b     # 对称差 {1, 4}
```

### 用途

- 去重：`list(set(items))`（会丢失顺序，有序去重用 dict）
- 成员检测：比 list 的 `in` 快得多
- 集合运算

### 冻结集合 frozenset

不可变集合，可作 dict 的键：

```python
fs = frozenset([1, 2, 3])
```

## 数据结构选择指南

| 需求 | 选择 |
|:---|:---|
| 有序可变序列 | list |
| 固定不可变记录 | tuple |
| 键值查找 | dict |
| 去重 / 集合运算 | set |
| 计数 | Counter |
| 分组 | defaultdict |

## 学习要点总结

1. dict 是哈希表，平均 O(1) 查找
2. 用 `get(key, default)` 避免 KeyError
3. set 自动去重，成员检测高效
4. `collections` 模块提供 defaultdict、Counter 等增强结构
5. 键必须可哈希：str、int、tuple 可以，list、dict 不行
