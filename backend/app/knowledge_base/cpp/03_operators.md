# C++ 运算符

## 运算符的本质

运算符是编译器内置或用户重载的**语法糖**，最终都归结为函数调用或机器指令。C++ 继承了 C 的全部运算符，并增加了流、作用域、内存管理等运算符。理解优先级、结合性和求值顺序，是写出正确、可读代码的基础。

### C 与 C++ 运算符扩展

| 运算符 | 含义 | C++ 特有 |
|:---|:---|:---|
| `<<` `>>` | 位移 / **流插入提取** | 流重载是 C++ 核心 I/O 机制 |
| `::` | **作用域解析** | 命名空间、类成员访问 |
| `.*` `->*` | **成员指针** | 指向类成员的指针 |
| `new` `delete` | **动态内存** | 构造/析构与分配绑定 |
| `typeid` | **运行时类型信息** | RTTI |
| `noexcept` | **异常说明** | 函数是否抛异常 |

## 算术运算符

与 C 相同：`+` `-` `*` `/` `%`

```cpp
int a = 7, b = 3;
std::cout << a / b << std::endl;   // 2（整数除法，截断小数）
std::cout << a % b << std::endl;   // 1

double x = 7.0 / 3;                // 2.333...（至少一个操作数是浮点）
```

### 整数溢出的深层理解

```cpp
int max = INT_MAX;
max + 1;   // 有符号整数溢出 → 未定义行为（UB）！
```

**原因**：C/C++ 标准对有符号溢出不做定义，编译器可假设"永不溢出"做激进优化，导致与直觉不符的结果。

```cpp
unsigned int u = UINT_MAX;
u + 1;   // 无符号溢出 → 按模 2ⁿ 运算，结果为 0（定义良好）
```

**防御式编程**：涉及溢出风险的运算使用更大类型、`#include <limits>` 检查，或 C++26 起关注安全整数提案。

## 关系与逻辑运算符

```cpp
// 关系：== != < > <= >=
// 逻辑：&& || !
// 短路求值：&& 和 || 不会计算不必要的右侧表达式

if (ptr != nullptr && *ptr > 0) { /* 安全：ptr 空时不解引用 */ }
if (vec.empty() || vec[0] == target) { /* vec 空时不访问 [0] */ }
```

**与 C 相同**：C++ 中 `bool` 是独立类型，但条件上下文仍接受可转为 `bool` 的表达式（指针、整数等）。

### 常见陷阱

```cpp
if (a = 5) { }   // 赋值，不是比较！几乎总是 bug
if (a == 5) { }  // 正确

if (!p == 0) { } // 等价于 (!p) == 0，即 true == 0，为假
                 // 可能本意是 p == nullptr
```

**原因**：`!` 优先级高于 `==`，应写 `p == nullptr` 或 `!p`（指针语境）。

## 位运算符

```cpp
int a = 0b1010;    // 10
int b = 0b1100;    // 12

a & b;   // 0b1000 = 8   按位与
a | b;   // 0b1110 = 14  按位或
a ^ b;   // 0b0110 = 6   按位异或
~a;      // 按位取反
a << 2;  // 左移：0b101000 = 40（相当于 ×2²）
a >> 1;  // 右移：0b0101 = 5（相当于 ÷2）
```

**右移的符号位**：对有符号负数，右移是实现定义（算术右移或逻辑右移）。无符号右移总是逻辑右移。

C++20 提供 `<bit>`：`std::popcount`、`std::countl_zero`、`std::has_single_bit` 等，比手写位运算更安全。

## 赋值与复合赋值

```cpp
int x = 10;
x += 5;    // x = x + 5，但 x 只求值一次
x *= b + c; // x = x * (b + c)，不是 (x * b) + c
```

**C++ 特有**：复合赋值运算符对自定义类型返回**左值引用**（如 `T& operator+=()`），支持链式 `a += b += c`。

```cpp
int a, b, c;
a = b = c = 0;   // 从右到左结合：c=0, b=0, a=0
```

## 自增自减

```cpp
int i = 5;
int a = i++;   // a=5, i=6（后置：先取值再自增，需保存旧值）
int b = ++i;   // b=7, i=7（前置：先自增再取值）

// 迭代器习惯用前置（避免拷贝临时对象）
for (auto it = v.begin(); it != v.end(); ++it) { }
```

### 未定义行为（与 C 相同）

```cpp
int i = 0;
int x = i++ + i++;   // 未定义行为！同一变量在两个序列点间修改两次
int y = ++i + ++i;   // 同样未定义
```

**原因**：C++ 不规定多个副作用的求值顺序（C++17 前对大多数运算符；C++17 起 `<<` 等部分有规定）。**不要在一表达式中对同一变量多次修改**。

## 条件运算符（三元）

```cpp
int max_val = (a > b) ? a : b;

// 两分支类型必须兼容，否则隐式转换
int a = 5;
double b = 3.14;
auto result = (a > 3) ? a : b;   // result 为 double
```

**C++11 起**：lambda 可作分支（需相同可调用类型或 `std::common_type`）。

## 逗号运算符

```cpp
int x = (a = 1, b = 2, a + b);   // x = 3，返回最后一个表达式

for (int i = 0, j = 10; i < j; ++i, --j) { }
```

**注意**：`int a = 1, 2, 3;` 是非法声明，不是逗号运算符！

## sizeof 运算符

```cpp
sizeof(int);           // 4（通常）
sizeof arr;            // 整个数组（arr 必须是数组名，非指针）
sizeof...(args);       // C++11：可变参数包中元素个数
```

**与 C 相同**：`sizeof` 是编译期运算符。数组作为函数参数退化为指针，`sizeof` 不再返回数组大小。

## 类型转换运算符

### C 风格（不推荐）

```cpp
double d = 3.14;
int i = (int)d;   // 或 int(d)，几乎无编译期检查
```

**问题**：可在任意类型间转换，包括 `const` 移除、指针reinterpret，难以搜索且易错。

### C++ 风格（推荐）

```cpp
// static_cast：编译期可检查的" sensible" 转换
int i = static_cast<int>(3.14);
void* p = static_cast<void*>(&obj);
Derived* d = static_cast<Derived*>(basePtr);  // 无运行时检查

// dynamic_cast：多态类型的安全向下转型（需虚函数）
Base* b = new Derived();
Derived* d = dynamic_cast<Derived*>(b);  // 失败返回 nullptr

// const_cast：仅添加或移除 const/volatile
const int ci = 10;
int* p = const_cast<int*>(&ci);  // 修改 ci 仍是 UB

// reinterpret_cast：底层比特重新解释（危险，仅 C/硬件互操作）
int x = 65;
char* c = reinterpret_cast<char*>(&x);
```

**原则**：
1. 优先 `static_cast`
2. 多态向下转型用 `dynamic_cast`
3. 避免 `const_cast` 修改原 const 对象
4. `reinterpret_cast` 仅在与 C API、硬件地址映射时使用

### 与 C 隐式转换的对比

C 在表达式中自动**整数提升**和**算术转换**；C++ 规则类似但更严格（如 `enum class` 不隐式转 int）。列表初始化 `{}` 拒绝窄化转换。

## 运算符优先级（从高到低）

| 优先级 | 运算符 | 结合性 |
|:---|:---|:---|
| 1 | `::` | 左 |
| 2 | `()` `[]` `->` `.` `++` `--`（后缀） | 左 |
| 3 | `++` `--`（前缀） `!` `~` `*` `&` `sizeof` | 右 |
| 4 | `*` `/` `%` | 左 |
| 5 | `+` `-` | 左 |
| 6 | `<<` `>>` | 左 |
| 7 | `<` `<=` `>` `>=` | 左 |
| 8 | `==` `!=` | 左 |
| 9 | `&` | 左 |
| 10 | `^` | 左 |
| 11 | `\|` | 左 |
| 12 | `&&` | 左 |
| 13 | `\|\|` | 左 |
| 14 | `?:` | 右 |
| 15 | `=` `+=` `-=` 等 | 右 |
| 16 | `,` | 左 |

**黄金规则**：复杂表达式**始终加括号**，不要依赖记忆优先级。

```cpp
int c = a & b == 1;   // 等价于 a & (b == 1)，不是 (a & b) == 1
```

## 流运算符 << 和 >>

```cpp
std::cout << "x = " << x << std::endl;   // 链式插入
std::cin >> n >> name;                    // 链式提取
```

**本质**：`operator<<` 和 `operator>>` 是**重载函数**，可为用户自定义类型扩展：

```cpp
std::ostream& operator<<(std::ostream& os, const MyType& obj) {
    return os << obj.value;
}
```

**与 C printf 对比**：类型安全，无需 `%d`/`%s` 格式串匹配。

### new 与 delete 运算符

```cpp
int* p = new int(42);        // 分配并构造
delete p;

int* arr = new int[10]();    // 分配 10 个 int，值初始化为 0
delete[] arr;                // 必须用 delete[] 释放数组
```

**与 C malloc/free 对比**：

| | C | C++ |
|:---|:---|:---|
| 分配 | `malloc` 只分配字节 | `new` 分配并**调用构造函数** |
| 释放 | `free` | `delete` 调用**析构函数**再释放 |
| 类型 | 返回 `void*` 需强转 | 返回正确类型指针 |
| 失败 | 返回 NULL | 默认抛 `std::bad_alloc` |

**现代 C++**：优先 `std::vector`、`std::unique_ptr`，避免裸 `new`/`delete`。详见内存管理章节。

### 作用域解析运算符 ::

```cpp
std::cout << std::endl;       // std 命名空间中的 endl
MyClass::memberFunc();        // 类 MyClass 的成员函数
::globalFunc();               // 全局命名空间（访问被局部 shadow 的全局名）
```

**本质**：告诉编译器去哪个作用域查找名字，编译期解析，零运行时开销。

## 运算符重载（预览）

```cpp
class Complex {
    double real, imag;
public:
    Complex operator+(const Complex& other) const {
        return {real + other.real, imag + other.imag};
    }
    friend std::ostream& operator<<(std::ostream& os, const Complex& c) {
        return os << c.real << "+" << c.imag << "i";
    }
};
```

**不能重载**：`::`、`.`、`.*`、`?:`、`sizeof`、`typeid`

**原则**：重载应遵循直觉（`+` 做加法，`<<` 做输出），不要创造令人困惑的语义。

## 常见错误

### 1. 优先级陷阱

见上文 `a & b == 1` 示例。

### 2. 浮点直接用 == 比较

```cpp
if (0.1 + 0.2 == 0.3) { }   // 几乎总是 false
```

**原因**：IEEE 754 表示误差。用 `std::abs(a-b) < epsilon`。

### 3. 有符号整数溢出

见算术运算符节，属于 UB。

### 4. 误用逗号运算符

```cpp
if (a = 1, b = 2) { }   // 条件实际是 b = 2 的结果，不是 a==1 && b==2
```

### 5. 移位超出位宽

```cpp
int x = 1;
x << 32;   // 未定义行为！移位量 ≥ 位宽（32 位 int 最多移 31 位）
x << -1;   // 同样未定义
```

**原因**：C/C++ 标准对移位量超出范围不做定义。防御：确保移位量在 `[0, sizeof(T)*8 - 1]` 内。

### 6. 对 bool 做位运算期望得到 bool

```cpp
bool a = true, b = false;
auto c = a & b;   // c 的类型是 bool，但 a 和 b 会先提升为 int 再运算
```

**建议**：逻辑组合用 `&&`/`||`，位运算仅用于整数类型。

## 学习要点总结

1. C++ 运算符是 C 的超集，新增了流、作用域、new/delete 等
2. 类型转换优先 C++ 风格 cast，避免 C 风格 `(type)`
3. 前置 `++` 对迭代器和自定义类型通常更高效
4. 同一表达式中不要对同一变量多次修改（UB）
5. 复杂表达式用括号；理解短路求值用于空指针检查
6. 有符号溢出是 UB，无符号溢出是模运算
7. 运算符重载应遵循直觉语义，不滥用
