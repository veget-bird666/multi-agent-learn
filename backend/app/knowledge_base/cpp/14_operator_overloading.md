# C++ 运算符重载

## 运算符重载的本质

### 为什么需要运算符重载

内置类型支持 `+`、`-`、`==` 等运算符；用户定义类型默认不支持。运算符重载允许**以自然语法**操作自定义类型：

```cpp
class Complex {
    double real, imag;
public:
    Complex(double r, double i) : real(r), imag(i) {}

    Complex operator+(const Complex& other) const {
        return Complex(real + other.real, imag + other.imag);
    }

    Complex& operator+=(const Complex& other) {
        real += other.real;
        imag += other.imag;
        return *this;
    }
};

Complex a(1, 2), b(3, 4);
Complex c = a + b;   // 等价于 a.operator+(b)
a += b;
```

**深层理解**：运算符重载本质是**语法糖**，`a + b` 编译为 `operator+(a, b)` 或 `a.operator+(b)`。不改变运算符优先级和结合性。

**C 对比**：C 无运算符重载，需用函数表达：

```c
Complex complex_add(Complex a, Complex b) {
    return (Complex){a.real + b.real, a.imag + b.imag};
}
```

## 作为成员函数 vs 自由函数

```cpp
class Vector {
    double x, y;
public:
    // 成员：左操作数隐式是 *this
    Vector operator+(const Vector& v) const {
        return Vector(x + v.x, y + v.y);
    }

    Vector operator-() const { return Vector(-x, -y); }   // 一元
};

// 自由函数：左操作数可以不是本类
Vector operator*(double scalar, const Vector& v) {
    return Vector(scalar * v.x, scalar * v.y);
}

std::ostream& operator<<(std::ostream& os, const Vector& v) {
    return os << "(" << v.x << ", " << v.y << ")";
}
```

### 选择规则

| 运算符 | 推荐形式 | 原因 |
|:---|:---|:---|
| `=`, `[]`, `()`, `->` | 必须是成员 | 语言规定 |
| `+=`, `-=`, `++`, `--` | 通常成员 | 修改 *this |
| `+`, `-`, `*`, `==`, `<<` | 通常自由函数 | 对称性（支持 `2 * v`） |
| `<<`, `>>` | 必须自由函数 | 左操作数是 stream |

**对称性示例**：

```cpp
// 仅成员 operator+ 时：
Vector v;
// 2 + v;   // 错误！2 不是 Vector

// 自由函数：
Vector operator+(double s, const Vector& v);
Vector operator+(const Vector& v, double s);
// 2 + v 和 v + 2 都 OK
```

## 常用运算符重载

### 比较运算符

```cpp
// C++20 三路比较（推荐）
#include <compare>

class Point {
    int x, y;
public:
    auto operator<=>(const Point& other) const = default;
    // 自动生成 ==, !=, <, <=, >, >=
};

// C++17 及之前
bool operator==(const Point& a, const Point& b) {
    return a.x == b.x && a.y == b.y;
}
bool operator<(const Point& a, const Point& b) {
    return std::tie(a.x, a.y) < std::tie(b.x, b.y);
}
```

**C 对比**：C 结构体不能 `==`，需 `memcmp` 或逐成员比较。

### 下标运算符

```cpp
class Array {
    std::vector<int> data;
public:
    int& operator[](size_t i) { return data[i]; }
    const int& operator[](size_t i) const { return data[i]; }
};
```

**防御性编程**：对外部输入用 `at()` 或在 `operator[]` 中断言/抛异常：

```cpp
int& operator[](size_t i) {
    if (i >= data.size()) throw std::out_of_range("index");
    return data[i];
}
```

### 函数调用运算符（仿函数）

```cpp
class Multiplier {
    int factor;
public:
    Multiplier(int f) : factor(f) {}
    int operator()(int x) const { return x * factor; }
};

Multiplier times3(3);
int result = times3(10);   // 30
```

**用途**：STL 算法自定义谓词、回调、std::function 的底层实现之一。

### 类型转换运算符

```cpp
class Fraction {
    int num, den;
public:
    explicit operator double() const {
        return static_cast<double>(num) / den;
    }
};

Fraction f(3, 4);
double d = static_cast<double>(f);   // OK
// double d2 = f;   // explicit 禁止隐式转换
```

**原因**：隐式转换运算符可能导致意外转换链和歧义。

## 输入输出流

```cpp
class Complex {
    double real, imag;
    friend std::ostream& operator<<(std::ostream& os, const Complex& c);
    friend std::istream& operator>>(std::istream& is, Complex& c);
};

std::ostream& operator<<(std::ostream& os, const Complex& c) {
    return os << c.real << "+" << c.imag << "i";
}

std::istream& operator>>(std::istream& is, Complex& c) {
    return is >> c.real >> c.imag;
}
```

**为何用友元**：`<<` 左操作数是 `ostream`，不能是 Complex 的成员（左操作数必须是类对象）。

**返回 `ostream&`**：支持链式 `cout << a << b`。

## 自增自减

```cpp
class Counter {
    int value;
public:
    Counter& operator++() {    // 前置 ++
        ++value;
        return *this;
    }
    Counter operator++(int) {  // 后置 ++，int 参数是占位
        Counter tmp = *this;
        ++value;
        return tmp;            // 返回旧值副本
    }
};
```

**区别**：
- 前置：先增，返回 `*this` 引用
- 后置：保存旧值，再增，返回旧值副本（多一次拷贝）

**C 对比**：C 内置类型前置/后置行为相同；自定义类型后置通常更慢。

## 赋值运算符

```cpp
class Widget {
public:
    Widget& operator=(const Widget& other) {
        if (this == &other) return *this;
        // 拷贝成员...
        return *this;
    }

    Widget& operator=(Widget&& other) noexcept {
        if (this == &other) return *this;
        // 移动成员...
        return *this;
    }
};
```

**返回 `*this` 引用**：支持链式赋值 `a = b = c`。

**三五法则**：若自定义拷贝/移动赋值，通常也需自定义析构等（见构造/析构章节）。

## 不可重载的运算符

以下运算符**不能**重载：

| 运算符 | 原因 |
|:---|:---|
| `::` | 作用域解析，非操作 |
| `.*` / `->*` | 成员指针访问 |
| `.` | 成员访问 |
| `?:` | 三元，语法结构 |
| `sizeof` | 编译期运算符 |
| `typeid` | RTTI |
| `alignof` | 对齐 |

## C++20 三路比较 `<=>`

```cpp
#include <compare>

struct Version {
    int major, minor;
    auto operator<=>(const Version&) const = default;
};

Version v1{1, 0}, v2{2, 0};
v1 < v2;    // true
v1 == v2;   // false
```

**`<=>` 返回类型**：
- `std::strong_ordering`：全序，等价不可区分
- `std::weak_ordering`：等价可区分（如 `-0.0` vs `0.0`）
- `std::partial_ordering`：浮点 NaN 等

`= default` 按成员逐字比较，自动生成 `==` 和 `<=>` 及派生比较。

## 最佳实践

1. **保持语义**：`+` 应像加法，`==` 应像相等，不滥用（如 `operator+` 做减法）
2. **对称性**：`a + b` 和 `b + a` 行为一致，二元算术/比较常用自由函数
3. **返回类型**：
   - 修改自身的（`+=`）→ 返回 `T&`
   - 产生新值的（`+`）→ 返回值 `T`
   - 流运算符 → 返回 `ostream&`/`istream&`
4. **const 正确**：不修改左操作数的加 `const`
5. **避免过度重载**：晦涩运算符（如 `operator<<` 做输出以外的事）降低可读性
6. **explicit 转换**：防止隐式转换歧义

## 常见错误

### 1. 返回局部对象的引用

```cpp
Complex& operator+(const Complex& a, const Complex& b) {
    Complex result(a.real + b.real, a.imag + b.imag);
    return result;   // 错误！局部对象销毁后引用悬空
}
// 修复：返回 Complex（值），非 Complex&
```

### 2. 忘记 const

```cpp
bool operator==(Complex& a, Complex& b);   // 无法比较 const 对象
// 修复：const Complex& 参数，成员函数加 const
```

### 3. 隐式转换导致歧义

```cpp
class A {
public:
    A(int);
    A operator+(const A&);
};
// A a = 1 + 2;   // 可能：int→A(1)，再 operator+(A, A) 或多次转换
// 修复：构造函数加 explicit
```

### 4. 成员 vs 自由函数选择错误

```cpp
// 仅成员 operator+ 时无法 0 + obj
// 修复：提供自由函数或友元
```

### 5. 后置 ++ 返回类型错误

```cpp
Counter& operator++(int);   // 错误！后置应返回值副本
Counter operator++(int);    // 正确
```

### 6. 未处理自赋值

```cpp
Widget& operator=(const Widget& other) {
    delete[] data;
    data = new char[other.size];   // 若 this == &other，已 delete 自身
    // 修复：if (this == &other) return *this;
}
```

### 7. operator<< 未处理错误状态

```cpp
std::istream& operator>>(std::istream& is, Complex& c) {
    if (!(is >> c.real >> c.imag)) return is;   // 传播 fail 状态
    return is;
}
```

## 防御性编程模式

### 1. 比较运算符用 C++20 <=> default

减少手写错误，自动生成完整比较集。

### 2. 算术运算符以自由函数 + 成员 += 实现

```cpp
Complex& Complex::operator+=(const Complex& o) { /* ... */ return *this; }
Complex operator+(Complex a, const Complex& b) {
    a += b;
    return a;   // NRVO/移动
}
```

### 3. 转换运算符加 explicit

```cpp
explicit operator bool() const;
```

### 4. 友元仅用于需要访问 private 的运算符

```cpp
friend std::ostream& operator<<(std::ostream&, const MyClass&);
```

### 5. 遵循零法则

若成员都是 `string`、`vector` 等，比较运算符 `= default` 即可。

## 运算符重载决策流程

```
需要重载运算符？
  ├─ 是否 = [] () -> ？ → 必须成员函数
  ├─ 是否 << >> ？ → 自由函数（友元）
  ├─ 是否二元且需对称（如 +）？ → 自由函数
  ├─ 是否修改 *this（如 +=）？ → 成员函数
  └─ 是否 C++20 可比类型？ → operator<=>(const T&) const = default
```

## 学习要点总结

1. 运算符重载是语法糖，让自定义类型用法接近内置类型
2. `=`, `[]`, `()`, `->` 必须成员；`<<`/`>>` 必须自由函数
3. 对称二元运算符（`+`, `==`）优先自由函数；修改自身的用成员
4. C++20 用 `operator<=>(const T&) const = default` 自动生成比较
5. 返回局部值的运算符返回值类型，不要返回引用
6. 转换运算符加 `explicit` 防止意外隐式转换
7. 保持语义直观，避免为了"酷"而滥用运算符
