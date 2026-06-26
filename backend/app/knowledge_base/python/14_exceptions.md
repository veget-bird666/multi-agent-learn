# Python 异常处理

## 异常机制

程序运行时错误会**抛出异常**，若不捕获则终止程序：

```python
10 / 0          # ZeroDivisionError
int("abc")      # ValueError
d = {}
d["key"]        # KeyError
```

## try / except / else / finally

```python
def safe_divide(a: float, b: float) -> float | None:
    try:
        result = a / b
    except ZeroDivisionError:
        print("除数不能为零")
        return None
    except TypeError as e:
        print(f"类型错误: {e}")
        return None
    else:
        print("计算成功")      # 无异常时执行
        return result
    finally:
        print("清理工作")      # 无论是否异常都执行
```

执行顺序：`try` →（异常则 `except`）→（无异常则 `else`）→ `finally`

## 常见内置异常

| 异常 | 触发场景 |
|:---|:---|
| `ValueError` | 值合法但不符合要求 |
| `TypeError` | 类型不对 |
| `KeyError` | dict 键不存在 |
| `IndexError` | 序列索引越界 |
| `FileNotFoundError` | 文件不存在 |
| `AttributeError` | 对象无该属性 |
| `ImportError` | 导入失败 |

## 抛出异常

```python
def set_age(age: int) -> None:
    if age < 0:
        raise ValueError("年龄不能为负")
    if age > 150:
        raise ValueError("年龄不合理")

def process(data):
    if not data:
        raise RuntimeError("数据为空，无法处理")
```

### 自定义异常

```python
class AppError(Exception):
    """应用基础异常。"""
    pass

class ValidationError(AppError):
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")
```

## 异常链

```python
try:
    risky()
except IOError as e:
    raise ProcessingError("处理失败") from e
```

`from e` 保留原始异常信息，便于调试。

## EAFP vs LBYL

Python 风格：**EAFP**（Easier to Ask Forgiveness than Permission）

```python
# EAFP — Python 推荐
try:
    value = d[key]
except KeyError:
    value = default

# LBYL — Look Before You Leap
if key in d:
    value = d[key]
else:
    value = default
```

并发场景下 EAFP 更安全（检查后状态可能已变）。

## 不要滥用 bare except

```python
# 错误：捕获一切，包括 KeyboardInterrupt
try:
    do_work()
except:
    pass

# 正确：捕获具体异常
try:
    do_work()
except (ValueError, IOError) as e:
    log(e)
```

## 学习要点总结

1. `try/except/else/finally` 四段式处理异常
2. 捕获具体异常类型，避免裸 `except`
3. 用 `raise` 主动抛出，`from` 保留异常链
4. 自定义异常类继承 `Exception`
5. Python 偏好 EAFP：先尝试，出错再处理
