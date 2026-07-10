# C++ 类与面向对象基础

## 类的本质

### 从 C 结构体到 C++ 类

C 的结构体将**数据**聚合在一起；C++ 的类在结构体基础上增加了**访问控制**、**成员函数**、**构造/析构**、**继承**等，实现**封装**与**抽象**。

```c
// C：数据与函数分离
struct Point {
    int x, y;
};
void point_move(struct Point *p, int dx, int dy) {
    p->x += dx;
    p->y += dy;
}
```

```cpp
// C++：数据与操作封装
class Point {
    int x, y;
public:
    void move(int dx, int dy) {
        x += dx;
        y += dy;
    }
    int getX() const { return x; }
};
```

**深层理解**：类是**用户定义类型（UDT）**，编译器为对象分配内存、调用构造函数、按访问规则检查成员访问。对象是类的**实例**。

## 类与对象

```cpp
class Rectangle {
public:
    double width;
    double height;

    double area() const {
        return width * height;
    }
};

Rectangle rect{3.0, 4.0};   // 聚合初始化
std::cout << rect.area();   // 12
```

### 对象的内存布局

```cpp
class Example {
    int a;       // 4 字节
    double b;    // 8 字节
    char c;      // 1 字节
};
// sizeof(Example) 通常 24（对齐填充），与 C 结构体规则相同
```

```
地址偏移:  0    4    8    9   10   11   12 ... 23
内容:     [ a ][pad][  b (8 bytes)  ][ c ][ padding... ]
```

**C vs C++**：成员对齐、padding 规则与 C 结构体一致；C++ 类可含成员函数（不占用对象内存，存储在代码段）、虚函数（可能增加 vptr）。

## 访问控制

```cpp
class BankAccount {
private:
    double balance;          // 外部不可直接访问

public:
    void deposit(double amount) {
        if (amount > 0) balance += amount;
    }
    double getBalance() const { return balance; }

protected:
    std::string accountType;   // 派生类可访问，外部不可
};
```

| 修饰符 | 类内 | 派生类 | 外部 |
|:---|:---|:---|:---|
| `public` | ✓ | ✓ | ✓ |
| `protected` | ✓ | ✓ | ✗ |
| `private` | ✓ | ✗ | ✗ |

**封装原则**：数据成员通常 `private`，通过 public 接口访问，在接口内维护**不变量**（如 `balance >= 0`）。

**对比 C**：C 结构体所有成员 public，无语言级访问控制，靠命名约定（如 `_private` 前缀）或不透明指针。

## struct vs class

```cpp
struct Point {
    int x, y;   // 默认 public
};

class PointClass {
    int x, y;   // 默认 private
};
```

**唯一区别**是默认访问级别。惯例：
- 纯数据、POD 风格 → `struct`
- 有不变量、复杂行为 → `class`

C++ 中 `struct` 与 `class` 能力完全等价（都可有构造函数、继承、虚函数等）。

## 成员函数与 const 正确性

```cpp
class Widget {
    int value;
    mutable int access_count;   // 可在 const 成员函数中修改
public:
    int getValue() const {       // 不修改逻辑状态
        ++access_count;          // OK：mutable
        return value;
    }
    void setValue(int v) { value = v; }
};
```

**const 成员函数**：
- 不能修改非 `mutable` 成员
- 可被 `const Widget` 对象调用
- 重载：`void func()` vs `void func() const`

```cpp
void print(const Widget& w) {
    w.getValue();      // OK
    // w.setValue(10); // 编译错误
}
```

**深层理解**：`const` 是**契约**，承诺不修改对象逻辑状态，使接口更清晰、编译器能检查误用。

## this 指针

每个非静态成员函数隐式接收 `this` 指针（类型 `T*` 或 `const T*`）：

```cpp
class Counter {
    int count;
public:
    Counter& increment() {
        ++count;
        return *this;   // 支持链式调用
    }
    int getCount() const { return count; }
};

Counter c;
c.increment().increment();
```

**注意**：`this` 是指针，`*this` 是当前对象的引用。静态成员函数无 `this`。

## 静态成员

```cpp
class MathUtils {
public:
    static const double PI;
    static int instance_count;
    static double circleArea(double r) {
        return PI * r * r;
    }
};

const double MathUtils::PI = 3.141592653589793;
int MathUtils::instance_count = 0;

// 调用
double area = MathUtils::circleArea(5.0);
```

**特点**：
- 属于**类**而非某个对象，所有实例共享
- 静态数据成员必须在类外**定义**（C++17 起 inline 静态可类内初始化）
- 静态成员函数无 `this`，只能访问静态成员

**对比 C**：类似 `static` 全局变量/函数，但作用域限制在类内，命名更清晰。

## 友元

```cpp
class Secret {
    friend class Trusted;           // 友元类
    friend void reveal(Secret& s);  // 友元函数
private:
    int data;
};

void reveal(Secret& s) {
    s.data = 42;   // 可访问 private
}
```

**本质**：友元是**访问控制机制的例外**，给予特定函数/类访问 private/protected 的权限。友元关系**不传递、不继承**。

**使用场景**：运算符重载（如 `<<`）、紧密耦合的类（如 iterator 与 container）、某些设计模式。

**原则**：优先 public 接口；友元破坏封装，仅在必要时使用。

## 嵌套类

```cpp
class Outer {
public:
    class Inner {
        int value;
    public:
        Inner(int v) : value(v) {}
        int get() const { return value; }
    };
};

Outer::Inner obj(10);
```

嵌套类可以是 private，用于实现细节隐藏（如 pimpl 的内部类）。

## 类内初始化（C++11）

```cpp
class Config {
    int port = 8080;
    std::string host{"localhost"};
    std::vector<int> ids{1, 2, 3};
};
```

成员初始化优先级：**初始化列表 > 类内默认值 > 默认构造**。

## 前向声明

```cpp
class Other;   // 前向声明，不需要完整定义

class MyClass {
    Other* ptr;      // OK：指针只需知道类型存在
    // Other member; // 错误：成员对象需要完整定义（需知 sizeof）
};
```

**作用**：减少头文件依赖，加快编译。指针/引用可前向声明；成员对象、继承、按值传参需完整定义。

## 设计原则

### 封装

隐藏实现细节，暴露稳定接口：

```cpp
class Stack {
    std::vector<int> data;   // private 实现细节
public:
    void push(int x) { data.push_back(x); }
    void pop() {
        if (!data.empty()) data.pop_back();
    }
    int top() const {
        if (data.empty()) throw std::runtime_error("empty stack");
        return data.back();
    }
    bool empty() const { return data.empty(); }
};
```

**对比 C**：C 常把 `struct` 暴露，或通过不透明指针 `typedef struct Stack Stack;` 隐藏实现。

### 不变量（Invariants）

类应维护内部一致性约束：

```cpp
class BankAccount {
    double balance;
public:
    void withdraw(double amount) {
        if (amount <= 0) throw std::invalid_argument("amount must be positive");
        if (amount > balance) throw std::runtime_error("insufficient funds");
        balance -= amount;
    }
    // balance >= 0 是不变量
};
```

**防御性编程**：所有 public 修改接口都验证输入，防止对象进入无效状态。

### 接口 vs 实现

- 头文件（.h）：类声明、public 接口
- 源文件（.cpp）：成员函数实现
- 减少编译依赖，隐藏实现细节

## C struct 与 C++ class 对比

| 特性 | C struct | C++ class |
|:---|:---|:---|
| 成员函数 | 无 | 有 |
| 访问控制 | 无 | public/protected/private |
| 构造函数 | 无 | 有 |
| 继承 | 无（C 无继承） | 有 |
| 运算符重载 | 无 | 有 |
| 内存布局 | 仅数据成员 | 数据成员 + 可能的 vptr |
| 比较 | 不能 `==` | 可重载 `==` |

## 常见错误

### 1. 头文件中定义非 inline 成员函数

```cpp
// header.h
class Foo {
    void bar() { /* 实现 */ }   // 若未 inline，多 .cpp include → 链接重复定义
};
// 原因：每个翻译单元都有一份定义
// 修复：类内 = default 或 inline；或实现放 .cpp
```

### 2. 忘记 const 正确性

```cpp
void print(const Widget& w) {
    w.setValue(10);   // 编译错误（正确行为）
}
// 原因：const 对象只能调用 const 成员函数
```

### 3. 直接暴露成员变量

```cpp
class Bad {
public:
    int age;   // 外部可设为 -1，破坏不变量
};
// 原因：无法强制执行验证逻辑
// 修复：private + getter/setter
```

### 4. 在构造函数中使用虚函数

```cpp
class Base {
public:
    Base() { init(); }
    virtual void init() {}
};
class Derived : public Base {
    void init() override { /* 派生逻辑 */ }
};
Derived d;   // Base 构造时 init() 调用 Base::init，非 Derived::init
// 原因：构造顺序中，派生部分尚未构造，虚函数机制绑定到当前已构造类型
```

### 5. 类内成员顺序与初始化顺序

成员按**声明顺序**初始化，与初始化列表顺序无关（见构造/析构章节）。

### 6. 忘记定义静态成员

```cpp
class X { static int count; };
// 必须在某 .cpp 中：int X::count = 0;
// 原因：声明不是定义，链接时需要唯一定义
```

## 防御性编程模式

### 1. 数据私有，接口公开

```cpp
class Account {
    double balance = 0;
public:
    void deposit(double amount);   // 验证后修改
};
```

### 2. 不变量在每个 public 入口检查

```cpp
void setAge(int a) {
    if (a < 0 || a > 150) throw std::invalid_argument("invalid age");
    age = a;
}
```

### 3. 优先 const 成员函数

能加 `const` 就加，使 const 对象可用、意图清晰。

### 4. 避免 public 数据成员

除 POD 数据包（如 `struct Vec3 { float x,y,z; };`）外，一般数据应 private。

### 5. 使用前向声明减少耦合

```cpp
class HeavyImpl;   // 前向声明
class Facade {
    std::unique_ptr<HeavyImpl> pimpl;
};
```

## 学习要点总结

1. 类 = 数据 + 操作 + 访问控制，是 C 结构体的超集
2. 数据成员 `private`，通过 public 方法访问，维护不变量
3. 不修改对象的成员函数声明为 `const`
4. 静态成员属于类，需在类外定义（除非 inline static）
5. `struct` 默认 public，`class` 默认 private，能力等价
6. 友元谨慎使用，优先 public 接口
7. 构造函数中虚函数不会多态到派生类
8. 成员对齐与 C 结构体相同，注意 padding 与 sizeof
