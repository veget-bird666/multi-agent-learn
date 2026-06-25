# Python 数据类型与变量

## 动态类型系统

Python 中**变量是对象的引用**，不是固定类型的内存盒子：

```python
x = 42        # x 引用 int 对象 42
x = "hello"   # x 改为引用 str 对象，合法
```

类型绑定在**对象**上，不在变量名上。

## 基本数据类型

| 类型 | 示例 | 说明 |
|:---|:---|:---|
| `int` | `42`, `-7`, `0b1010` | 任意精度整数 |
| `float` | `3.14`, `1e-5` | 双精度浮点 |
| `bool` | `True`, `False` | 布尔，是 int 子类 |
| `str` | `"hello"`, `'world'` | 不可变字符序列 |
| `NoneType` | `None` | 空值，类似其他语言的 null |

### 类型查看与转换

```python
type(42)           # <class 'int'>
isinstance(3.0, float)  # True

int("42")          # 42
float("3.14")      # 3.14
str(100)           # "100"
bool(0)            # False
bool("")           # False
bool("hi")         # True
```

### 整数任意精度

```python
10 ** 100   # 正常计算，不会溢出
```

### 浮点精度陷阱

```python
0.1 + 0.2 == 0.3   # False！
round(0.1 + 0.2, 1)  # 0.3
```

金融计算应使用 `decimal.Decimal`。

## 变量命名

```python
user_name = "Alice"   # snake_case，推荐
MAX_SIZE = 100        # 常量习惯全大写
_private = 1          # 单下划线：内部使用约定
```

**保留字**不可作变量名：`if`, `for`, `class`, `def`, `import` 等。

## 可变 vs 不可变

| 不可变 | 可变 |
|:---|:---|
| int, float, bool, str, tuple | list, dict, set |

```python
s = "hello"
s[0] = "H"   # TypeError: str 不可变

lst = [1, 2, 3]
lst[0] = 99  # 合法，原地修改
```

理解可变性对理解函数参数传递至关重要。

## 赋值机制

### 引用赋值

```python
a = [1, 2, 3]
b = a          # b 和 a 引用同一列表
b.append(4)
print(a)       # [1, 2, 3, 4]
```

### 拷贝

```python
import copy

b = a.copy()           # 浅拷贝
c = copy.deepcopy(a)   # 深拷贝（嵌套结构时用）
```

## 身份 vs 相等

```python
a = [1, 2]
b = [1, 2]
a == b    # True  值相等
a is b    # False 不是同一对象
a is a    # True  身份相同
```

- `==`：值相等
- `is`：是否为同一对象（常用来与 `None` 比较：`x is None`）

## 学习要点总结

1. Python 变量是对象的引用，类型在对象上
2. 基本类型：int、float、bool、str、None
3. 区分可变（list/dict/set）与不可变（str/tuple/int）类型
4. 浮点数有精度问题，比较时用 `round` 或 `decimal`
5. `==` 比价值，`is` 比身份
