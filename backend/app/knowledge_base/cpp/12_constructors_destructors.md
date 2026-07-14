# C++ 构造函数与析构函数

## 特殊成员函数的本质

C++ 对象生命周期由**特殊成员函数**管理。编译器在特定时机自动调用它们：

| 时机 | 函数 |
|:---|:---|
| 创建对象 | 构造函数 |
| 销毁对象 | 析构函数 |
| 用同类对象初始化 | 拷贝构造函数 |
| 同类对象赋值 | 拷贝赋值运算符 |
| 从临时对象"窃取" | 移动构造 / 移动赋值（C++11） |

**深层理解**：C 语言无构造函数/析构函数，资源管理靠手动 `init`/`cleanup` 函数；C++ 将资源获取绑定到构造、释放绑定到析构（RAII）。

## 构造函数

对象创建时自动调用，用于初始化成员：

```cpp
class Person {
    std::string name;
    int age;
public:
    Person() : name("Unknown"), age(0) {}   // 默认构造

    Person(const std::string& n, int a) : name(n), age(a) {}

    Person(const std::string& n) : Person(n, 0) {}   // 委托构造（C++11）
};
```

### 构造函数调用时机

```cpp
Person p1;                    // 默认构造
Person p2("Alice", 30);       // 带参构造
Person p3 = p2;               // 拷贝构造（不是赋值！）
Person p4 = Person("Bob", 25); // 拷贝省略（C++17 起通常无拷贝）
auto p5 = Person("Carol", 28); // 同上
```

## 成员初始化列表

```cpp
class Point {
    const int id;
    int& ref;
    std::string name;
public:
    Point(int i, int& r, const std::string& n)
        : id(i), ref(r), name(n) {}
};
```

**必须用初始化列表的情况**：
- `const` 成员（只能初始化一次）
- 引用成员（必须绑定有效对象）
- 没有默认构造函数的成员对象
- 基类（需指定基类构造函数）

**效率**：直接初始化优于"默认构造 + 赋值"：

```cpp
// 低效
Person(const std::string& n) {
    name = n;   // 先 default 构造 name，再 operator= 赋值
}

// 高效
Person(const std::string& n) : name(n) {}   // 直接拷贝构造
```

### 初始化顺序陷阱

成员按**声明顺序**初始化，与初始化列表顺序无关：

```cpp
class Demo {
    int a;
    int b;
public:
    Demo(int x) : b(x), a(b) {}   // 危险！先初始化 a（用未初始化的 b）
};
```

**生命周期图**：

```
声明顺序: a, b
初始化:   a ← (b 尚未初始化，UB)  →  b ← x
```

**防御性编程**：初始化列表顺序与成员声明顺序一致。

## 析构函数

对象销毁时自动调用（栈展开、delete、作用域结束）：

```cpp
class FileHandler {
    std::fstream file;
public:
    FileHandler(const std::string& path) {
        file.open(path);
    }
    ~FileHandler() {
        if (file.is_open()) file.close();
    }
};
```

**RAII 核心**：析构是资源释放的最后防线，即使发生异常也会调用。

### 析构顺序

1. 派生类析构函数体
2. 派生类成员（声明逆序）
3. 基类析构函数

```cpp
{ FileHandler fh("data.txt"); }   // 离开作用域 → ~FileHandler 自动调用
```

**注意**：析构函数**不应抛异常**。若抛异常且已有异常在传播，会调用 `std::terminate`。

## 拷贝构造函数

用同类型**已有对象**初始化**新对象**：

```cpp
class String {
    char* data;
    size_t len;
public:
    String(const char* s);
    String(const String& other);   // 拷贝构造
};

String::String(const String& other) : len(other.len) {
    data = new char[len + 1];
    std::copy(other.data, other.data + len + 1, data);
}
```

**默认拷贝**：编译器生成的拷贝构造是**逐成员拷贝**（浅拷贝）。含指针/资源成员时通常不够。

### 浅拷贝 vs 深拷贝

```
浅拷贝（默认）:
  a.data ──→ [ "hello" ]
  b.data ──→ [ 同一地址 ]   ← 析构时 double free！

深拷贝（自定义）:
  a.data ──→ [ "hello" ]
  b.data ──→ [ "hello" ]   ← 独立副本
```

**C 对比**：C 结构体赋值是逐成员拷贝（`struct a = b`），同样浅拷贝；C++ 类可自定义拷贝语义。

## 拷贝赋值运算符

```cpp
String& String::operator=(const String& other) {
    if (this == &other) return *this;   // 自赋值检查

    delete[] data;                       // 释放旧资源
    len = other.len;
    data = new char[len + 1];
    std::copy(other.data, other.data + len + 1, data);
    return *this;
}
```

**拷贝赋值 vs 拷贝构造**：
- 构造：`String b = a;` — 创建新对象
- 赋值：`b = a;` — 已有对象，先释放旧资源再拷贝

### 异常安全的 copy-and-swap

```cpp
String& operator=(String other) {   // 按值传参 = 拷贝
    swap(*this, other);             // 交换
    return *this;
}   // other 析构，自动释放旧资源
// 若拷贝中途抛异常，*this 未被修改
```

**原因**：先 `delete` 再 `new`，若 `new` 失败则对象已损坏；copy-and-swap 保证强异常安全。

## 移动构造与移动赋值（C++11）

```cpp
String(String&& other) noexcept
    : data(other.data), len(other.len) {
    other.data = nullptr;
    other.len = 0;
}

String& operator=(String&& other) noexcept {
    if (this == &other) return *this;
    delete[] data;
    data = other.data;
    len = other.len;
    other.data = nullptr;
    other.len = 0;
    return *this;
}
```

**移动语义**："窃取"临时对象的资源，避免深拷贝：

```
移动前:  temp.data ──→ [ heap buffer ]
        other.data ──→ nullptr

移动后:  other.data ──→ [ heap buffer ]
         temp.data ──→ nullptr（可安全析构）
```

**C 无对应概念**：C 只能 memcpy 或手动转移指针。

## 三五法则与零法则

### 三五法则（Rule of Five）

若类需要自定义以下**任一项**，通常需要自定义**全部五项**：

| 特殊成员 | 作用 |
|:---|:---|
| 析构函数 | 释放资源 |
| 拷贝构造 | 深拷贝 |
| 拷贝赋值 | 深拷贝 |
| 移动构造 | 转移资源 |
| 移动赋值 | 转移资源 |

**原因**：资源管理类若自定义析构（说明有手动资源），默认拷贝/移动往往是错的。

### 零法则（Rule of Zero）

若成员都是 RAII 类型（`string`、`vector`、`unique_ptr`），**不要**自定义任何特殊成员：

```cpp
class Modern {
    std::string name;
    std::vector<int> data;
    // 编译器生成的特殊成员已正确：深拷贝、移动、析构
};
```

**现代 C++ 推荐**：优先用 RAII 成员，遵循零法则。

## explicit 关键字

防止单参数构造函数的**隐式转换**：

```cpp
class Distance {
    double meters;
public:
    explicit Distance(double m) : meters(m) {}
};

Distance d(100.0);      // OK：直接初始化
// Distance d2 = 100.0;  // 错误：explicit 禁止隐式转换
Distance d3 = Distance(100.0);  // OK：显式构造
```

**原因**：隐式转换可能导致意外类型转换和重载歧义。

## 默认与删除函数（C++11）

```cpp
class NonCopyable {
public:
    NonCopyable() = default;
    NonCopyable(const NonCopyable&) = delete;
    NonCopyable& operator=(const NonCopyable&) = delete;
};

class WithDefault {
    std::vector<int> data;   // 有默认构造的成员
public:
    WithDefault() = default;   // 编译器生成
};
```

`= delete` 比 private 且不实现更清晰，会在调用点直接编译错误。

## 完整构造/析构顺序

### 构造顺序

1. 基类构造函数（按继承顺序）
2. 成员对象（按**声明顺序**）
3. 构造函数体

### 析构顺序

1. 构造函数体（析构函数体）
2. 成员对象（按声明**逆序**）
3. 基类析构函数（按继承逆序）

```
class Derived : public Base {
    Member m1;
    Member m2;
public:
    Derived() : Base(), m1(), m2() { /* 体 */ }
};

构造: Base → m1 → m2 → 体
析构: 体 → m2 → m1 → ~Base
```

## 常见错误

### 1. 浅拷贝导致双重释放

```cpp
String a("hello");
String b = a;   // 默认浅拷贝
// a 和 b 析构时都 delete[] 同一指针
// 原因：未自定义拷贝构造/析构
// 修复：深拷贝，或改用 std::string
```

### 2. 忘记自赋值检查

```cpp
String& operator=(const String& other) {
    delete[] data;   // 若 this == &other，删除自身数据
    // ...
}
// 修复：if (this == &other) return *this;
```

### 3. 异常不安全的赋值

```cpp
String& operator=(const String& other) {
    delete[] data;
    data = new char[other.len + 1];   // 若 new 抛 bad_alloc，*this 已损坏
    // ...
}
// 修复：copy-and-swap
```

### 4. 在析构函数中抛异常

```cpp
~Foo() {
    cleanup();   // 若抛异常且已有异常传播 → std::terminate
}
// 修复：析构函数内捕获并吞掉，或 noexcept
```

### 5. 初始化列表顺序与声明不一致

见上文 Demo 类示例。原因：标准规定按声明顺序初始化。

### 6. 虚析构缺失（继承场景）

```cpp
class Base { ~Base() {} };   // 非 virtual
Base* p = new Derived();
delete p;   // 只调用 ~Base，Derived 部分泄漏
// 修复：virtual ~Base() = default;
```

## 防御性编程模式

### 1. 遵循零法则

```cpp
class User {
    std::string name;
    std::vector<int> scores;
};
```

### 2. 必须管理资源时用 Rule of Five + move noexcept

```cpp
class Buffer {
    char* data;
    size_t size;
public:
    Buffer(Buffer&& other) noexcept;
    Buffer& operator=(Buffer&& other) noexcept;
    // 移动 noexcept 帮助 vector 等容器优化
};
```

### 3. 单参数构造函数加 explicit

除非确实需要隐式转换（如 `string(const char*)` 在 std 库中允许）。

### 4. 用 = delete 禁止拷贝

```cpp
class Singleton {
    Singleton(const Singleton&) = delete;
};
```

### 5. 初始化列表初始化所有成员

避免部分成员未初始化（尤其内置类型）。

## 学习要点总结

1. 用**初始化列表**初始化成员，尤其是 const、引用、无默认构造的成员
2. 成员初始化顺序由**声明顺序**决定，与初始化列表顺序无关
3. 含手动资源管理时遵循**三五法则**；用 RAII 成员时遵循**零法则**
4. 单参数构造函数考虑加 `explicit`
5. 移动语义避免不必要的深拷贝；移动操作标记 `noexcept` 利于容器优化
6. 拷贝赋值需自赋值检查；优先 copy-and-swap 保证异常安全
7. 析构函数不抛异常；多态基类析构函数应 `virtual`
