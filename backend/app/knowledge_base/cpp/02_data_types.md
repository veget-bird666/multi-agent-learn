# C++ 数据类型与变量

## 数据类型的本质

C++ 继承了 C 的**强类型静态类型系统**，并在其上大幅扩展。每个变量在编译时就必须确定类型，因为类型决定了：

- **内存占用大小**：`int` 通常 4 字节，`double` 通常 8 字节
- **存储与解释方式**：同样的二进制 `0x40400000`，作为 `int` 是 1077936128，作为 `float` 是 3.0
- **合法操作**：不能对 `int` 做字符串拼接；`bool` 与指针的语义不同
- **名字修饰与重载**：C++ 按类型参与函数重载决议

### C 与 C++ 类型系统对比

| 特性 | C | C++ |
|:---|:---|:---|
| 布尔类型 | `_Bool`（C99）/ 用 int 模拟 | 内置 `bool`，关键字 `true`/`false` |
| 空指针 | `NULL`（可能是 0 或 `(void*)0`） | `nullptr`，类型安全 |
| 字符串 | `char[]` + 手动管理 | `std::string`（RAII） |
| 类型推断 | 无 | `auto`、`decltype`（C++11） |
| 编译期常量 | `#define`、`enum` 有限 | `constexpr` 编译期求值 |
| 引用 | 无 | `int&` 别名，无空引用 |
| 强类型枚举 | 传统 `enum` 泄漏到外层 | `enum class`（C++11） |
| 统一初始化 | 仅部分支持 | `{}` 列表初始化，防窄化 |

## 基本数据类型

### 整数类型家族

| 类型 | 最小范围（有符号） | 典型大小 | 字面量后缀 |
|:---|:---|:---|:---|
| `char` | -128 ~ 127 | 1 字节 | — |
| `short` | ±32767 | 2 字节 | — |
| `int` | ±2×10⁹ | 4 字节 | — |
| `long` | 平台相关 | 4 或 8 字节 | `L` |
| `long long` | ±9×10¹⁸ | 8 字节 | `LL` |

```cpp
unsigned int u = 42u;
long long big = 9223372036854775807LL;
auto hex = 0xFF;          // 十六进制
auto bin = 0b1010;        // 二进制（C++14）
auto sep = 1'000'000;     // 数字分隔符（C++14，提高可读性）
```

**有符号 vs 无符号陷阱**（与 C 相同）：

```cpp
unsigned int u = 10;
int s = -1;
if (s < u) {
    // 期望成立，实际不成立！
}
// 原因：s 被提升为 unsigned int，-1 的二进制 0xFFFFFFFF 被解释为 4294967295
```

**C++ 改进**：比较混合符号时，显式转换或使用 `std::cmp_*`（C++20 `<utility>`）更安全。

### 浮点类型

| 类型 | 精度 | 典型大小 | 有效数字 |
|:---|:---|:---|:---|
| `float` | 单精度 | 4 字节 | 6-7 位 |
| `double` | 双精度 | 8 字节 | 15-16 位 |
| `long double` | 扩展精度 | 12/16 字节 | 18-21 位 |

```cpp
float f = 3.14f;
double d = 3.141592653589793;
long double ld = 3.14L;

// 浮点比较（与 C 相同，不能直接用 ==）
#include <cmath>
if (std::abs(a - b) < 1e-9) { /* 近似相等 */ }
```

**原因**：`0.1` 在二进制中是无限循环小数，存储时截断导致 `0.1 + 0.2 != 0.3`。

### 布尔类型

```cpp
bool flag = true;
bool result = (5 > 3);    // true

// 输出：0 或 1（不是 "true"/"false"）
std::cout << flag << std::endl;
std::cout << std::boolalpha << flag << std::endl;  // 输出 true

// 条件中自动转为 bool
if (42) { /* 非零即真，与 C 相同 */ }
```

**与 C 对比**：C99 的 `_Bool`/`bool` 在 C++ 中就是原生 `bool`；C++ 不允许 `bool` 与指针隐式混用（更安全）。

### 字符与字符串

```cpp
char c = 'A';              // ASCII 65
wchar_t wc = L'中';         // 宽字符
char16_t u16 = u'中';       // UTF-16 码元
char32_t u32 = U'中';       // UTF-32 码点

const char* s = "Hello";    // C 风格字符串，只读字面量
std::string str = "Hello";  // C++ 字符串（推荐，RAII 管理内存）

// 原始字符串字面量（C++11），避免转义地狱
auto raw = R"(Line1
Line2)";                    // 含换行的多行字符串
auto json = R"({"key": "value"})";
```

**深层理解**：`"Hello"` 的类型是 `const char[6]`（含 `\0`），可退化为 `const char*`。`std::string` 在堆或 SSO（小字符串优化）中存储，自动管理生命周期。

## auto 与 decltype

### auto 类型推断

```cpp
auto i = 42;                    // int
auto d = 3.14;                  // double
auto s = std::string("hi");     // std::string
auto v = std::vector<int>{1, 2, 3};

int x = 10;
auto& ref = x;                  // int&，ref 是 x 的别名
auto* ptr = &x;                 // int*

const int ci = 10;
auto a = ci;                    // int，丢弃顶层 const
const auto b = ci;              // const int
```

**本质**：`auto` 让编译器从**初始化表达式**推导类型，是编译期特性，零运行时开销。

**陷阱**：

```cpp
auto& r = some_function();  // 若返回临时对象，绑定到 const auto& 可延长生命周期
                            // 非 const auto& 绑定临时对象是危险的
```

**最佳实践**：复杂迭代器、lambda 类型用 `auto`；简单类型（如 `int i = 0`）显式写出有时更清晰。

### decltype

```cpp
int x = 0;
decltype(x) y = 1;        // int
decltype((x)) z = x;    // int& —— 注意：(x) 是左值表达式，类型为 int&

template<typename T, typename U>
auto add(T a, U b) -> decltype(a + b) {  // C++11 尾置返回类型
    return a + b;
}
```

**C++14 起**：`decltype(auto)` 保留引用和 cv 限定，常用于转发函数。

## const 与 constexpr

### const 常量

```cpp
const int MAX = 100;
const int* p = &MAX;       // 指向常量的指针（不能通过 p 改值）
int* const q = &x;         // 常量指针（q 不能改指向）
const int* const r = &MAX; // 两者都是 const

// 常量成员函数（类中）
class Widget {
    int getValue() const { return value; }  // 承诺不修改对象状态
private:
    int value;
};
```

**与 C 对比**：C 的 `const` 可通过指针强转绕过；C++ 同样存在 `const_cast`，但语义上 `const` 对象不应被修改，违反则未定义行为。

### constexpr 编译期常量

```cpp
constexpr int square(int x) {
    return x * x;
}

constexpr int result = square(5);  // 编译期计算，可用于数组大小、模板参数

// C++14 起 constexpr 函数可以有多条语句
constexpr int factorial(int n) {
    int r = 1;
    for (int i = 1; i <= n; ++i) r *= i;
    return r;
}

int arr[factorial(4)];   // 数组大小 24，编译期确定
```

**const vs constexpr**：

| | const | constexpr |
|:---|:---|:---|
| 求值时机 | 可能运行时 | 必须编译期可求值 |
| 用途 | 只读变量 | 编译期常量、数组大小、模板实参 |
| 对比 C | 类似 `#define` 的只读替代 | C 无直接等价物 |

**原因**：`constexpr` 保证编译期已知，比 `#define` 有类型检查和作用域，比 `const` 约束更强。

## nullptr

```cpp
void func(int);
void func(char*);

func(NULL);     // 歧义！NULL 可能是 0，调用 func(int)
func(nullptr);  // 明确调用 func(char*)，类型 std::nullptr_t

int* p = nullptr;
if (p == nullptr) { /* 空指针 */ }
```

**原因**：`NULL` 在 C 中常定义为 `0` 或 `(void*)0`，在 C++ 重载决议中可能匹配 `int` 而非指针。`nullptr` 是**空指针字面量**，只能转为指针类型，类型安全。

## 类型别名

```cpp
typedef unsigned long ulong;           // C 风格，仍可用

using uint = unsigned int;             // C++11，更清晰
template<typename T>
using Vec = std::vector<T>;            // 模板别名（typedef 做不到）

Vec<int> numbers;   // std::vector<int>
```

## 枚举类型

### 传统 enum（不推荐）

```cpp
enum Color { RED, GREEN, BLUE };
enum Color c = RED;

if (c == 0) { }   // 可以编译！枚举隐式转 int，污染外层作用域
```

**问题**：枚举值泄漏到外层（`RED` 可直接使用）；隐式转 `int`，类型不安全。

### 强类型枚举 enum class（推荐）

```cpp
enum class Color { Red, Green, Blue };
enum class Status : uint8_t { Ok = 0, Error = 1 };  // 指定底层类型

Color c = Color::Red;
// if (c == 0) { }   // 错误！不能隐式转 int
if (c == Color::Red) { /* 正确 */ }

int i = static_cast<int>(c);   // 需显式转换
```

**C++ 改进**：作用域限定（`Color::Red`）、无隐式转整型、可指定底层类型节省空间。

## 变量初始化（C++11 统一初始化）

```cpp
int a = 10;           // 拷贝初始化
int b(20);            // 直接初始化
int c{30};            // 列表初始化（推荐，防止窄化）
int d = {40};

// 窄化检测
int e{3.14};          // 错误！double → int 窄化，列表初始化拒绝
int f = 3.14;         // 警告但允许（拷贝初始化不检测窄化）

struct Point { int x, y; };
Point p{1, 2};

std::vector<int> v{1, 2, 3, 4, 5};
```

**防御式编程**：优先 `{}` 初始化，编译器帮你捕获精度丢失等错误。

### 声明 vs 定义

```cpp
extern int x;      // 声明：告诉编译器 x 在其他翻译单元定义
int x = 10;        // 定义：分配存储并初始化
```

**规则**：变量只能**定义**一次（ODR），可**声明**多次。与 C 相同。

### 未初始化局部变量

```cpp
int x;
std::cout << x;   // 未定义行为！值不确定
```

**原因**：局部变量在栈上分配，编译器不保证初始值。全局/静态变量零初始化。C++ 与 C 行为一致——**必须初始化**。

## sizeof 与 typeid

```cpp
std::cout << sizeof(int) << std::endl;       // 通常 4
std::cout << sizeof(void*) << std::endl;     // 64 位系统通常 8

int arr[10];
std::cout << sizeof(arr) << std::endl;       // 40（整个数组）
// 传给函数后 arr 退化为指针，sizeof 不再等于数组大小

#include <typeinfo>
std::cout << typeid(42).name() << std::endl; // 类型名（编译器相关，可能 mangled）
```

**与 C 相同**：`sizeof` 是编译期运算符，不是函数。数组作为函数参数退化为指针。

## 常见错误

### 1. auto 推导丢失 const 和引用

```cpp
const int ci = 10;
auto x = ci;        // x 是 int，不是 const int
const auto y = ci;  // 正确保留 const
```

### 2. NULL 导致重载歧义

见上文 `nullptr` 节。

### 3. 列表初始化与 std::initializer_list 混淆

```cpp
std::vector<int> v{1, 2, 3};     // 初始化 3 个元素
std::vector<int> v2(10, 0);      // 10 个 0
// std::vector<int> v3{10, 0};   // 两个元素 10 和 0，不是 10 个 0！
```

**原因**：`{10, 0}` 匹配 `initializer_list`，`(10, 0)` 匹配 `(count, value)` 构造函数。

### 4. 有符号与无符号比较

见整数类型陷阱，与 C 完全相同。

## 学习要点总结

1. C++ 在 C 类型基础上增加了 `bool`、`nullptr`、引用、`enum class`、`constexpr`
2. `auto` 从初始化式推导类型；`decltype` 从表达式推导类型
3. `constexpr` 用于编译期计算，比 `#define` 和单纯 `const` 更安全、更有表达力
4. 优先 `enum class` 而非传统 `enum`；优先 `nullptr` 而非 `NULL`
5. 花括号 `{}` 初始化能防止窄化，是 C++11 推荐的统一初始化方式
6. 局部变量必须初始化；混合有符号/无符号比较要格外小心
7. 固定大小数组考虑 `std::array`，字符串用 `std::string`，见后续章节
