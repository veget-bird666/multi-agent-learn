# C++ 函数

## 函数的本质

函数是 C++ 程序的基本构建块。从底层看，函数调用涉及：

1. **参数传递**：按值、引用或指针将实参传给形参
2. **栈帧建立**：保存返回地址、局部变量、寄存器
3. **跳转执行**：PC 指向函数入口
4. **返回**：返回值写入约定位置（寄存器或栈），恢复栈帧，跳回调用处

C++ 在 C 基础上增加了**函数重载、默认参数、引用、inline、constexpr、模板、lambda** 等，使函数成为更强大的抽象单元。

## 函数声明与定义

```cpp
// 声明（通常在头文件 .h / .hpp）
int add(int a, int b);
double add(double a, double b);   // 重载

// 定义（通常在 .cpp 文件）
int add(int a, int b) {
    return a + b;
}
```

**声明 vs 定义**：
- **声明**：告诉编译器函数名、参数类型、返回值；不分配代码
- **定义**：提供函数体，生成机器码

**为什么需要声明？** 编译器单遍扫描。若定义在使用之后，没有声明则 C++ 直接报错（C99 前 C 有隐式 int 声明，已废弃）。

### 与 C 对比

| | C | C++ |
|:---|:---|:---|
| 函数重载 | 不支持 | 支持，靠名字修饰 |
| 默认参数 | 不支持 | 支持 |
| 引用参数 | 无，用指针 | `int&` 别名 |
| 内联 | C99 `inline` | `inline`，ODR 规则更复杂 |
| 编译期函数 | 无 | `constexpr` |

## 参数传递机制

### 值传递

```cpp
void increment(int x) {
    ++x;   // 修改的是形参副本
}

int main() {
    int n = 5;
    increment(n);
    // n 仍为 5
}
```

**本质**：将实参**拷贝**到形参。与 C 完全相同。

### 引用传递（C++ 特有）

```cpp
void increment(int& x) {
    ++x;   // 直接修改原变量，无拷贝
}

void print(const std::string& s) {
    // const 引用：只读，避免拷贝大对象，也不能修改 s
    std::cout << s << std::endl;
}
```

**引用 vs 指针**：

```
值传递:  实参 n ──拷贝──→ 形参 x（独立内存）
引用:    实参 n ←──────→ 形参 x（同一内存，别名）
指针:    实参 n ←── ptr 指向（可 nullptr，可算术）
```

**原因**：引用是别名，编译器通常实现为指针，但语法更安全（不能为空、不能重新绑定）。

**防御式编程**：大对象只读参数用 `const T&`；需要修改用 `T&`；小对象（`int`、`double`）值传递即可。

### 指针传递

```cpp
void swap(int* a, int* b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// 现代 C++ 优先引用
void swap_ref(int& a, int& b) {
    std::swap(a, b);
}
```

| 方式 | 能否修改实参 | 拷贝开销 | 典型用途 |
|:---|:---|:---|:---|
| 值传递 | 否 | 有 | 小对象、需要副本 |
| 引用 | 是 | 无 | 修改参数 |
| const 引用 | 否 | 无 | 只读大对象（推荐） |
| 指针 | 是 | 无 | C 互操作、可选参数（可 nullptr） |

## 函数重载

同一作用域内，函数名相同但**参数列表不同**（类型或数量）：

```cpp
int abs_int(int x)       { return x < 0 ? -x : x; }
long abs_long(long x)    { return x < 0 ? -x : x; }
double abs_double(double x) { return x < 0 ? -x : x; }

// 或使用不同名 + 重载
int abs(int x);
long abs(long x);
double abs(double x);

abs(-5);      // int 版本
abs(-5L);     // long 版本
abs(-3.14);   // double 版本
```

**底层**：编译器通过**名字修饰**生成不同符号（如 `_Z3absi`、`_Z3absd`），链接器据此区分。

**不能仅靠返回值重载**：

```cpp
int  func();
double func();   // 错误！调用 func() 时编译器无法仅凭返回值选择
```

**重载决议**：编译器按**最佳匹配**选择；无匹配或二义性均编译错误。

### 重载与默认参数的冲突

```cpp
void func(int x);
void func(int x, int y = 0);   // 调用 func(5) 产生歧义！
```

**原因**：两个函数都能匹配 `func(5)`。

## 默认参数

```cpp
void greet(const std::string& name, const std::string& prefix = "Hello") {
    std::cout << prefix << ", " << name << "!" << std::endl;
}

greet("Alice");              // Hello, Alice!
greet("Bob", "Hi");          // Hi, Bob!
```

**规则**：
- 默认参数从**右向左**连续出现
- 声明和定义中默认参数**只能出现一次**（通常在头文件声明中）
- 默认参数在**调用点**编译期绑定，不是运行时

```cpp
void func(int a = 1, int b);   // 错误！a 有默认值但 b 没有
```

## 内联函数

```cpp
inline int square(int x) {
    return x * x;
}
```

**本质**：`inline` 是**建议**编译器在调用处展开代码，消除函数调用开销（压栈、跳转）。

**注意**：
- 编译器可能忽略 `inline`
- 定义通常放头文件（每个翻译单元需看到完整定义以满足 ODR）
- 现代编译器自动内联小函数，不必过度标注

**与 C 对比**：C99 也有 `inline`，但 C++ 的 ODR（单一定义规则）对 inline 函数更宽松——inline 函数可在多个翻译单元定义。

## constexpr 函数

编译期可执行的函数：

```cpp
constexpr int factorial(int n) {
    return (n <= 1) ? 1 : n * factorial(n - 1);
}

constexpr int result = factorial(5);   // 120，编译期计算
int arr[factorial(4)];                 // 数组大小 24

// C++14 起可含循环
constexpr int sum(int n) {
    int s = 0;
    for (int i = 1; i <= n; ++i) s += i;
    return s;
}
```

**用途**：编译期常量、数组大小、模板参数、`if constexpr` 配合。C 无直接等价物。

## 函数模板（初步）

```cpp
template<typename T>
T maximum(T a, T b) {
    return (a > b) ? a : b;
}

maximum(3, 5);        // T = int
maximum(3.14, 2.71);  // T = double
```

**本质**：编译器根据实参类型**实例化**具体函数，类似宏但类型安全。详见模板章节。

## Lambda 表达式（初步）

```cpp
auto add = [](int a, int b) { return a + b; };
std::cout << add(3, 4) << std::endl;   // 7

int factor = 2;
auto scale = [factor](int x) { return x * factor; };  // 按值捕获
auto scale_ref = [&factor](int x) { return x * factor; };  // 按引用捕获
```

**用途**：STL 算法回调、短生命周期 functor。C 需写函数指针或宏。

## 递归

```cpp
unsigned long long factorial(unsigned n) {
    if (n <= 1) return 1;           // 基准情况
    return n * factorial(n - 1);    // 递归情况
}
```

### 栈帧与栈溢出

```
factorial(3) 调用
  → factorial(2) 调用（栈上多一层）
    → factorial(1) 返回 1
  → 返回 2
→ 返回 6
```

**陷阱**：
- 缺少基准情况 → 无限递归 → 栈溢出（Stack Overflow）
- 朴素斐波那契 O(2ⁿ)，应用记忆化或迭代

```cpp
// 尾递归形式（编译器可能优化为循环，但不保证）
int factorial_tail(int n, int acc = 1) {
    if (n <= 1) return acc;
    return factorial_tail(n - 1, n * acc);
}
```

**C 对比**：规则相同；C++ 可用 `constexpr` 递归在编译期求值（有深度限制）。

## 函数指针与 std::function

```cpp
using BinaryOp = int(*)(int, int);

int add(int a, int b) { return a + b; }
BinaryOp op = add;
op(3, 4);   // 7

// C++11 推荐：类型擦除，可存 lambda
#include <functional>
std::function<int(int, int)> f = add;
f = [](int a, int b) { return a * b; };
```

**语法**：`返回类型 (*指针名)(参数列表)`

## 返回值

### 返回基本类型

按值返回，拷贝（小对象通常被 RVO/NRVO 优化消除拷贝）。

### 返回引用/指针的危险

```cpp
// 致命错误！
const std::string& bad() {
    std::string s = "hello";
    return s;   // 返回局部变量的引用，s 已销毁 → 悬垂引用
}

// 正确：返回值（拷贝/MOVE）或返回静态/堆对象
std::string good() {
    return "hello";   // RVO 可能消除拷贝
}
```

**原因**：局部变量在栈上，函数返回后栈帧销毁，引用/指针指向无效内存。

### 返回 std::vector 等（C++11 移动语义）

```cpp
std::vector<int> make_vec() {
    std::vector<int> v = {1, 2, 3};
    return v;   // 移动语义，通常无拷贝开销
}
```

## 常见错误

### 1. 返回局部变量引用

见上文。**原因**：悬垂引用，UB。

### 2. 默认参数与重载冲突

见重载节。

### 3. 头文件中定义非 inline 非模板函数

```cpp
// header.h
void foo() { }   // 多个 .cpp include → 链接错误：重复定义
```

**解决**：声明在头文件，定义在 `.cpp`；或标记 `inline`；或使用模板。

### 4. 忽略 const 正确性

```cpp
void process(std::string s);           // 每次调用拷贝
void process(const std::string& s);    // 推荐
```

### 5. 声明与定义签名不一致

```cpp
// a.cpp
int func(int x);

// b.cpp
double func(double x) { ... }   // 链接可能不报错，运行时参数传递错误！
```

**防御**：头文件统一声明，所有翻译单元 include 同一头文件。

### 6. 递归无基准 / 栈溢出

大局部数组 + 深递归：

```cpp
void deep(int n) {
    char buf[4096];   // 每层 4KB
    deep(n - 1);      // 递归过深 → 栈溢出
}
```

## 学习要点总结

1. 大对象只读参数用 `const T&`，小对象或需副本用值传递；修改用 `T&`
2. 函数重载依据参数列表，不能仅靠返回值区分
3. 默认参数放声明中，从右向左连续；避免与重载产生歧义
4. `constexpr` 函数可在编译期求值；`inline` 建议头文件定义
5. 不要返回局部变量的引用或指针；返回值类型通常安全（有 RVO）
6. 引用是 C++ 相对 C 的核心改进，优先于指针（除非需要 nullptr）
7. 递归必须有基准情况；注意栈深度与重复计算
