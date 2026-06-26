# Python 运算符

## 算术运算符

```python
10 + 3    # 13
10 - 3    # 7
10 * 3    # 30
10 / 3    # 3.333...  真除法，结果是 float
10 // 3   # 3         地板除
10 % 3    # 1         取模
2 ** 10   # 1024      幂运算
```

| 运算符 | 说明 |
|:---|:---|
| `/` | 真除法，至少一方是 float 则结果为 float |
| `//` | 地板除，向负无穷取整 |
| `**` | 幂，右侧结合 |

```python
-7 // 2   # -4  不是 -3
```

## 比较运算符

```python
3 == 3    # True
3 != 5    # True
3 < 5     # True
3 >= 3    # True
```

**链式比较**（Python 特色）：

```python
1 < x < 10      # 等价于 1 < x and x < 10
a == b == c     # 三者相等
```

## 逻辑运算符

```python
True and False   # False
True or False    # True
not True         # False
```

### 短路求值

```python
def side_effect():
    print("called")
    return True

False and side_effect()  # 不打印
True or side_effect()    # 不打印
```

### 返回值技巧

`and` / `or` 返回**操作数本身**，不一定是 bool：

```python
"" or "default"     # "default"
"name" or "guest"   # "name"
x = a if condition else b   # 三元表达式
```

## 成员与身份运算符

```python
"a" in "abc"        # True
3 in [1, 2, 3]      # True
x is None           # 身份比较
x is not None
```

## 位运算符

```python
5 & 3    # 1   AND
5 | 3    # 7   OR
5 ^ 3    # 6   XOR
~5       # -6  按位取反
5 << 1   # 10  左移
5 >> 1   # 2   右移
```

常用于标志位、权限掩码。

## 赋值运算符

```python
x = 10
x += 5      # x = x + 5
x *= 2
a, b = 1, 2           # 多重赋值
a, b = b, a           # 交换
first, *rest = [1,2,3,4]  # first=1, rest=[2,3,4]
```

## 运算符优先级（从高到低）

| 优先级 | 运算符 |
|:---|:---|
| 最高 | `**` |
| | 一元 `+ - ~` |
| | `* / // %` |
| | `+ -` |
| | 移位 `<< >>` |
| | 位与 `&` |
| | 位异或 `^` |
| | 位或 `\|` |
| | 比较 `== != < > <= >=` |
| | `not` |
| | `and` |
| | `or` |
| 最低 | 赋值 `=` |

不确定时用**括号**明确优先级。

## 学习要点总结

1. `/` 是真除法，`//` 是地板除，注意负数地板除行为
2. 链式比较 `a < b < c` 是 Python 特有语法
3. `and`/`or` 短路求值，且可能返回非 bool 值
4. `is` 用于身份比较，`==` 用于值比较
5. 多重赋值和 `*rest` 解包是常用惯用法
