# Python 面向对象编程

## 类与对象

```python
class Dog:
    species = "Canis familiaris"   # 类变量

    def __init__(self, name: str, age: int):
        self.name = name           # 实例变量
        self.age = age

    def bark(self) -> str:
        return f"{self.name} says woof!"

    def __str__(self) -> str:
        return f"Dog({self.name}, {self.age})"

dog = Dog("Buddy", 3)
dog.bark()
print(dog)
```

- `__init__`：构造方法，初始化实例
- `self`：实例自身，必须作为第一个参数
- `__str__`：`print()` 时显示的字符串

## 封装

Python 无真正的 private，用命名约定：

```python
class Account:
    def __init__(self, balance: float):
        self._balance = balance      # 单下划线：内部使用
        self.__secret = "key"        # 双下划线：名称改写

    def deposit(self, amount: float) -> None:
        if amount > 0:
            self._balance += amount

    @property
    def balance(self) -> float:
        return self._balance
```

`@property` 把方法变成属性访问：

```python
acc = Account(100)
print(acc.balance)   # 100，无需括号
```

## 继承

```python
class Animal:
    def __init__(self, name: str):
        self.name = name

    def speak(self) -> str:
        raise NotImplementedError

class Cat(Animal):
    def speak(self) -> str:
        return f"{self.name} says meow"

class Dog(Animal):
    def speak(self) -> str:
        return f"{self.name} says woof"
```

### super()

```python
class Employee:
    def __init__(self, name: str, salary: float):
        self.name = name
        self.salary = salary

class Manager(Employee):
    def __init__(self, name: str, salary: float, department: str):
        super().__init__(name, salary)
        self.department = department
```

### 多态

```python
def make_speak(animal: Animal) -> None:
    print(animal.speak())

make_speak(Cat("Whiskers"))
make_speak(Dog("Buddy"))
```

同一接口，不同行为。

## 特殊方法（魔术方法）

| 方法 | 触发 |
|:---|:---|
| `__init__` | 构造 |
| `__str__` / `__repr__` | 字符串表示 |
| `__len__` | `len(obj)` |
| `__getitem__` | `obj[key]` |
| `__eq__` | `==` 比较 |
| `__add__` | `+` 运算 |

```python
class Vector:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"
```

## 类方法与静态方法

```python
class Date:
    def __init__(self, year: int, month: int, day: int):
        self.year, self.month, self.day = year, month, day

    @classmethod
    def from_string(cls, s: str) -> "Date":
        y, m, d = map(int, s.split("-"))
        return cls(y, m, d)

    @staticmethod
    def is_leap(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

Date.from_string("2024-06-25")
Date.is_leap(2024)
```

| 装饰器 | 第一个参数 | 用途 |
|:---|:---|:---|
| 实例方法 | `self` | 操作实例 |
| `@classmethod` | `cls` | 工厂方法、操作类 |
| `@staticmethod` | 无 | 与类逻辑相关但不依赖实例 |

## dataclass（Python 3.7+）

简化数据类定义：

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0

p = Point(1.0, 2.0)
p.x = 3.0
```

自动生成 `__init__`、`__repr__`、`__eq__` 等。

## 学习要点总结

1. 类封装数据和行为，`self` 代表实例
2. 继承 + 多态实现代码复用和统一接口
3. `@property` 提供受控的属性访问
4. 特殊方法让自定义类支持 `+`、`len()`、`print()` 等操作
5. 简单数据类优先用 `@dataclass`
