# C++ 模板

## 模板是什么：编译期代码生成

C 语言实现泛型需要 `void*` 或宏，前者丢失类型安全，后者无类型检查且难调试。C++ 模板在**编译期**根据实参类型生成具体代码，兼顾类型安全与零运行时开销。

```
源代码（模板定义）
    ↓
编译器遇到 Stack<int>、Stack<string>
    ↓
实例化生成 Stack<int>、Stack<string> 两份具体类代码
    ↓
链接时合并相同实例化（ODR）
```

**与 C 宏对比**：

| 特性 | C 宏 | C++ 模板 |
|:---|:---|:---|
| 类型检查 | 无 | 有 |
| 调试 | 展开后难追踪 | 可单步进入实例化代码 |
| 代码膨胀 | 文本替换 | 每个类型一份实例 |
| 适用场景 | 简单常量/条件编译 | 泛型函数、容器、算法 |

## 函数模板

```cpp
template<typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

maximum(3, 5);         // 隐式实例化 T = int
maximum(3.14, 2.71);   // T = double
maximum<int>(3, 5);    // 显式指定 T
```

### 模板参数推断规则

编译器从实参推断 `T`，常见情况：

```cpp
template<typename T>
void func(T a, T b);

func(1, 2);        // T = int
func(1, 2.0);      // 错误！T 无法同时是 int 和 double

template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {
    return a + b;
}
add(1, 2.0);       // T=int, U=double，返回 double
```

**C++14 起**可省略尾置返回类型，编译器自动推断：

```cpp
template<typename T, typename U>
auto add(T a, U b) {
    return a + b;
}
```

### 非模板参数重载 vs 模板

```cpp
int maximum(int a, int b) { return (a > b) ? a : b; }   // 普通函数

template<typename T>
T maximum(T a, T b) { return (a > b) ? a : b; }         // 模板

maximum(3, 5);    // 优先调用普通函数（精确匹配）
maximum(3.0, 5.0); // 调用模板 double 版本
```

## 类模板

```cpp
template<typename T>
class Stack {
    std::vector<T> data;
public:
    void push(const T& value) { data.push_back(value); }
    void pop() {
        if (data.empty()) throw std::out_of_range("empty stack");
        data.pop_back();
    }
    T& top() { return data.back(); }
    const T& top() const { return data.back(); }
    bool empty() const { return data.empty(); }
    size_t size() const { return data.size(); }
};

Stack<int> intStack;
Stack<std::string> strStack;   // 必须显式指定类型参数
```

**函数模板 vs 类模板**：

| | 函数模板 | 类模板 |
|:---|:---|:---|
| 类型推断 | 可自动推断 | 必须显式指定（C++17 CTAD 除外） |
| 实例化时机 | 调用时 | 使用时 |
| 典型用途 | 算法、工具函数 | 容器、智能指针 |

### 类模板 CTAD（C++17）

```cpp
std::pair p(1, 2.0);           // pair<int, double>
std::vector v = {1, 2, 3};     // vector<int>
Stack s;                       // 若定义 deduction guides
```

## 模板参数种类

### 类型参数

```cpp
template<typename T, typename U = int>   // 默认类型参数
class Pair {
    T first;
    U second;
};
```

### 非类型参数（NTTP）

```cpp
template<typename T, size_t N>
class FixedArray {
    T data[N];
public:
    static constexpr size_t size() { return N; }
    T& operator[](size_t i) { return data[i]; }
    const T& operator[](size_t i) const { return data[i]; }
};

FixedArray<int, 10> arr;   // N=10 是编译期常量
// FixedArray<int, n> bad; // 错误！n 必须是编译期常量
```

**C 对比**：类似 `#define SIZE 10` + `int arr[SIZE]`，但模板保留类型信息。

C++20 起非类型参数可以是浮点、类类型（有限制）：

```cpp
template<std::floating_point auto Value>
struct Constant { static constexpr auto value = Value; };
```

### 模板模板参数

```cpp
template<typename T, template<typename> class Container>
class Wrapper {
    Container<T> c;
public:
    void add(const T& v) { c.push_back(v); }   // 要求 Container 有 push_back
};

Wrapper<int, std::vector> w1;
Wrapper<int, std::deque> w2;
```

## 模板特化

### 全特化

为特定类型提供完全不同的实现：

```cpp
template<>
class Stack<bool> {
    std::vector<uint8_t> bits;   // 位压缩实现
    // ...
};
```

### 偏特化（仅类模板）

```cpp
template<typename T>
class Container { /* 通用 */ };

template<typename T>
class Container<T*> { /* 指针特化 */ };

template<typename T>
class Container<const T> { /* const 特化 */ };
```

**函数模板不支持偏特化**，只能重载或全特化。

## 可变参数模板（C++11）

```cpp
template<typename... Args>
void log(Args&&... args) {
    (std::cout << ... << args) << '\n';   // C++17 左折叠
}

log("value=", 42, ", pi=", 3.14);
```

### sizeof... 与递归展开

```cpp
template<typename T>
void print(T&& t) {
    std::cout << t << '\n';
}

template<typename T, typename... Rest>
void print(T&& first, Rest&&... rest) {
    std::cout << first << ' ';
    print(std::forward<Rest>(rest)...);
}
```

## typename 与 class

模板参数中 `typename T` 与 `class T` **完全等价**：

```cpp
template<class T> void f1(T x) {}
template<typename T> void f2(T x) {}
```

在模板**内部**，`typename` 还有第二含义——标识**依赖类型名**：

```cpp
template<typename T>
void func() {
    typename T::value_type v;   // 没有 typename，编译器不知道这是类型
    T::template nested<U> obj;  // 依赖模板成员需 template 关键字
}
```

## 模板实例化机制

### 隐式 vs 显式

```cpp
Stack<int> s;   // 隐式实例化整个类

// 显式实例化声明（.h 中）
extern template class Stack<int>;

// 显式实例化定义（一个 .cpp 中）
template class Stack<int>;
```

**显式实例化用途**：大型模板只在少数 .cpp 中实例化，减少编译时间和二进制体积。

### 两阶段名字查找

- **第一阶段**：模板定义时，查找非依赖名字（如 `std::vector`）
- **第二阶段**：实例化时，查找依赖名字（如 `T::foo`）

## 模板与头文件

模板定义通常必须放在头文件中：

```cpp
// stack.h
template<typename T>
class Stack {
    std::vector<T> data;
public:
    void push(const T& value);   // 声明
};

// 必须在头文件末尾或 .tpp 中
template<typename T>
void Stack<T>::push(const T& value) {
    data.push_back(value);
}
```

**原因**：编译器实例化时需要看到完整定义。若定义在 .cpp，其他翻译单元链接时会报 `undefined reference`。

**例外**：显式实例化 + `extern template` 声明，适用于已知有限类型集合的库。

## SFINAE 与 Concepts

### SFINAE（Substitution Failure Is Not An Error）

替换失败不是错误——模板替换失败时，该重载从候选集中移除，而非编译错误：

```cpp
template<typename T>
typename std::enable_if<std::is_integral_v<T>, T>::type
double_value(T x) {
    return x * 2;
}

template<typename T>
typename std::enable_if<std::is_floating_point_v<T>, T>::type
double_value(T x) {
    return x * 2.0;
}
```

### Concepts（C++20）

```cpp
#include <concepts>

template<std::integral T>
T add(T a, T b) {
    return a + b;
}

template<typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

template<Addable T>
T sum(T a, T b) { return a + b; }
```

| 方式 | 错误信息 | 可读性 |
|:---|:---|:---|
| 无约束模板 | 冗长，指向深层实例化 | 差 |
| SFINAE | 中等 | 一般 |
| Concepts | 直接指出约束不满足 | 好 |

## 模板元编程简介

编译期计算，结果在编译期确定：

```cpp
template<int N>
struct Factorial {
    static constexpr int value = N * Factorial<N - 1>::value;
};

template<>
struct Factorial<0> {
    static constexpr int value = 1;
};

constexpr int f5 = Factorial<5>::value;   // 120，编译期算出
```

C++14/17 起 `constexpr` 函数通常比递归模板更清晰，优先使用 `constexpr`。

## 常见错误与陷阱

### 1. 模板定义放 .cpp

```cpp
// stack.cpp 中只有定义，stack.h 只有声明
Stack<int> s;
s.push(1);   // 链接错误：undefined reference to Stack<int>::push
```

**原因**：链接阶段找不到实例化代码。**修复**：定义放头文件，或显式实例化。

### 2. 类型推断失败

```cpp
maximum(3, 3.14);   // 错误
maximum<double>(3, 3.14);   // 显式指定
// 或写两个模板参数的版本
```

**原因**：一个模板参数 `T` 无法同时匹配 `int` 和 `double`。

### 3. 依赖名字解析错误

```cpp
template<typename T>
void bad() {
    T::value_type v;   // 错误！编译器不知道 value_type 是类型
}
```

**原因**：两阶段查找中，依赖名字需 `typename` 关键字。

### 4. 模板代码膨胀

每个 `(模板, 类型参数)` 组合生成一份代码，过多实例化增大二进制。

**缓解**：类型擦除（`std::function`）、显式实例化、共享实现（void* 内部 + 类型安全包装）。

### 5. 过度模板元编程

可读性急剧下降。**原则**：先用简单模板 + `constexpr` + Concepts，确有必要再元编程。

## 学习要点总结

1. 模板是**编译期**代码生成，实现类型安全的泛型，无运行时多态开销
2. 函数模板可推断类型，类模板需显式指定（C++17 CTAD 可推断部分）
3. 模板定义一般放头文件，或用显式实例化控制编译时间
4. **特化**为特定类型定制实现；函数模板用重载代替偏特化
5. C++20 **Concepts** 约束模板参数，显著改善错误信息
6. 理解 SFINAE 与两阶段名字查找，读懂 STL 源码的基础
