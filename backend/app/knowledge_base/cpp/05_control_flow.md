# C++ 控制流

## 控制流的本质

控制流语句决定程序**执行路径**：顺序、分支、循环、跳转。C++ 继承了 C 的 `if`、`switch`、`for`、`while`、`do-while`、`break`、`continue`、`goto`，并增加了**范围 for**、**基于范围的算法**、**C++17 初始化 if/switch**、**if constexpr** 等现代特性。

从底层看，分支和循环最终编译为**条件跳转**和**比较指令**；`switch` 常被优化为**跳转表**（O(1) 查找）。

## 条件语句

### if / else if / else

```cpp
int score = 85;

if (score >= 90) {
    std::cout << "A" << std::endl;
} else if (score >= 80) {
    std::cout << "B" << std::endl;
} else if (score >= 60) {
    std::cout << "C" << std::endl;
} else {
    std::cout << "F" << std::endl;
}
```

### 条件表达式的本质（与 C 对比）

C++ 有原生 `bool`，但条件仍接受可转为 `bool` 的表达式：

```cpp
if (x) { }           // 等价于 if (x != 0)（整数）
if (!x) { }          // 等价于 if (x == 0)
if (ptr) { }         // 等价于 if (ptr != nullptr)
if (str.empty()) { } // 显式成员函数，比 C 字符串更安全
```

**C 对比**：C 用整数 0/非 0；C++ `bool` 严格为 `true`/`false`，但 `if (42)` 仍合法（非零即真）。

**浮点陷阱**（与 C 相同）：

```cpp
double d = 0.0;
if (d == 0) { }      // 危险！浮点误差
if (std::abs(d) < 1e-9) { }  // 正确
```

### 悬空 else 问题

```cpp
if (condition1)
    if (condition2)
        std::cout << "A\n";
    else
        std::cout << "B\n";   // else 属于内层 if
```

**规则**：`else` 与**最近的未匹配** `if` 配对。

**黄金规则**：始终使用大括号，即使只有一行。

### 防御式编程：提前返回

```cpp
// 好的写法：先处理错误，减少嵌套
std::ifstream in("data.txt");
if (!in.is_open()) {
    std::cerr << "Cannot open file\n";
    return 1;
}
// 主逻辑在此，无需深层 if 嵌套

// 避免"箭头代码"
if (in.is_open()) {
    if (valid) {
        if (ready) {
            // 三层嵌套...
        }
    }
}
```

### C++17 初始化 if

```cpp
if (auto it = map.find(key); it != map.end()) {
    std::cout << it->second << std::endl;
}  // it 的作用域仅限 if 块及其 else

if (std::unique_ptr<Foo> p = make_foo(); p && p->valid()) {
    p->process();
}
```

**优势**：缩小变量作用域，避免命名泄漏到外层；比 C 的"先声明再 if"更紧凑安全。

## switch 语句

### 基本语法

```cpp
enum class Op { Add, Sub, Mul, Div };

Op op = Op::Add;
int a = 10, b = 5;
int result;

switch (op) {
    case Op::Add: result = a + b; break;
    case Op::Sub: result = a - b; break;
    case Op::Mul: result = a * b; break;
    case Op::Div:
        if (b != 0) result = a / b;
        else { std::cerr << "Division by zero!" << std::endl; return 1; }
        break;
    default:
        std::cerr << "Unknown operation" << std::endl;
        return 1;
}
```

### switch 的底层实现

编译器常将 `switch` 优化为**跳转表**：

```
switch 表达式值 → 查表 → 跳转到对应 case 标签
时间复杂度 O(1)，优于长 if-else 链
```

**case 标签要求**：必须是**编译期整型常量**（整数、枚举值、C++11 起 `constexpr`）。不能是浮点、字符串、运行时变量。

### 穿透（fall-through）

```cpp
switch (x) {
    case 1:
        doSomething();   // 缺少 break → 穿透到 case 2
    case 2:
        doOther();
        break;
}
```

**原因**：设计用于多 case 共享逻辑，但多数情况是 bug。C++17 起可用 `[[fallthrough]]` 属性显式标注 intentional fall-through。

### C++17 switch 初始化

```cpp
switch (auto c = getchar(); c) {
    case 'a': /* ... */ break;
    case 'q': return 0;
    default: break;
}
```

### 与 C 的对比

| | C | C++ |
|:---|:---|:---|
| case 类型 | 整型/枚举 | 同左，推荐 `enum class` |
| 变量在 case 中 | C99 需在块 `{}` 内 | C++17 可 switch 初始化 |
| 字符串 switch | 不支持 | C++ 仍不支持，用 map/if |

## 循环语句

### 传统 for 循环

```cpp
for (int i = 0; i < 10; ++i) {
    std::cout << i << " ";
}
```

**执行顺序**：初始化 → 条件检查 → 循环体 → 增量 → 条件检查 → ...

**防御式编程**：循环变量用 `++i`（前置），边界用 `< size` 而非 `<= size-1` 减少 off-by-one。

### 范围 for（C++11，推荐）

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

for (int x : v) {              // 拷贝（小对象可接受）
    std::cout << x << " ";
}

for (const auto& item : v) {   // const 引用，只读大对象（推荐）
    std::cout << item << " ";
}

for (auto& item : v) {         // 非 const 引用，修改元素
    item *= 2;
}
```

**本质**：编译器展开为基于 `begin()`/`end()` 的迭代器循环：

```cpp
// 近似等价
for (auto it = v.begin(), end = v.end(); it != end; ++it) {
    auto& item = *it;
}
```

**要求**：容器或数组有 `begin()`/`end()`（包括 C 数组、STL 容器、`initializer_list`）。

**C 对比**：C 只有索引 for 或指针遍历；范围 for 更安全、可读性更高。

### C++20 结构化绑定

```cpp
std::map<std::string, int> scores = {{"Alice", 90}, {"Bob", 85}};
for (const auto& [name, score] : scores) {
    std::cout << name << ": " << score << std::endl;
}
```

### while 循环

```cpp
int n;
std::cout << "Enter positive number: ";
while (std::cin >> n, n <= 0) {   // 逗号表达式：读入并检查
    std::cout << "Invalid, try again: ";
}
```

### do-while 循环

```cpp
int choice;
do {
    std::cout << "Menu: 1=Add 2=Exit\nChoice: ";
    std::cin >> choice;
} while (choice != 2);
```

**特点**：至少执行一次，适合菜单驱动程序。

## 跳转语句

### break 与 continue

```cpp
for (int i = 0; i < 100; ++i) {
    if (i % 2 == 0) continue;   // 跳过本次，进入下一次迭代
    if (i > 20) break;            // 跳出整个循环
    std::cout << i << " ";
}
```

### return

```cpp
std::optional<size_t> find(const std::vector<int>& v, int target) {
    for (size_t i = 0; i < v.size(); ++i) {
        if (v[i] == target) return i;
    }
    return std::nullopt;   // C++17，比返回 -1 更安全
}
```

### goto（避免使用）

```cpp
for (...) {
    for (...) {
        if (error) goto cleanup;
    }
}
cleanup:
    // 释放资源
```

**现代 C++**：用 RAII（智能指针、容器）和异常替代大多数 `goto`。仅在 C 风格资源清理或内核代码中偶见。

## 编译期条件：if constexpr（C++17）

```cpp
template<typename T>
auto process(T value) {
    if constexpr (std::is_integral_v<T>) {
        return static_cast<int>(value);
    } else {
        return static_cast<double>(value);
    }
}
```

**本质**：在**编译期**决定分支，未选中的分支**不参与编译**（模板实例化时丢弃）。与普通 `if` 不同——普通 `if` 两分支都会实例化，可能导致编译错误。

**用途**：模板元编程、泛型代码中按类型分支。

## 三元运算符与条件赋值

```cpp
int max_val = (a > b) ? a : b;
std::string status = (score >= 60) ? "Pass" : "Fail";

// 避免嵌套过深
int grade = score >= 90 ? 4 : score >= 80 ? 3 : score >= 60 ? 2 : 1;
// 可读性差，建议 switch 或查表
```

## 逻辑运算符与短路

```cpp
if (ptr != nullptr && ptr->isValid()) { }   // ptr 空时不调用 isValid()
if (!vec.empty() && vec[0] == x) { }        // 空时不访问 [0]

std::string name = input.empty() ? "Anonymous" : input;
```

**与 C 相同**：`&&` 和 `||` 短路求值，右侧可能不执行。

## 常见错误

### 1. switch 中忘记 break

```cpp
switch (x) {
    case 1: doSomething();   // 穿透到 case 2，通常是 bug
    case 2: doOther(); break;
}
```

### 2. 范围 for 中的不必要拷贝

```cpp
for (auto item : large_vector) { }           // 每次拷贝，性能差
for (const auto& item : large_vector) { }    // 正确
```

**原因**：`auto` 按值拷贝元素；大对象（如 `std::string`、自定义类）应用引用。

### 3. 浮点数 switch

```cpp
switch (3.14) { }   // 编译错误！case 必须是整型常量
```

### 4. 循环边界 off-by-one

```cpp
for (int i = 0; i <= v.size(); ++i) { }   // 越界！应为 i < v.size()
```

### 5. 在 range-for 中修改容器导致迭代器失效

```cpp
for (auto& x : v) {
    v.push_back(0);   // 可能 reallocate，引用/迭代器失效 → UB
}
```

### 6. 无限循环忘记退出条件

```cpp
while (true) {
    if (should_exit) break;   // 必须有 break 或 return
}
```

## 学习要点总结

1. 优先使用**范围 for** 遍历容器；大对象用 `const auto&`，修改用 `auto&`
2. C++17 的 `if (init; condition)` 和 `switch` 初始化缩小变量作用域
3. `switch` 必须配合 `break`（或 intentional `[[fallthrough]]`），`case` 需编译期常量
4. `if constexpr` 用于模板中的编译期分支，未选中分支不编译
5. 始终用大括号；浮点比较用 epsilon；防御式编程先处理错误路径
6. 避免 `goto`，用 RAII 和异常管理资源
7. range-for 中不要修改正在遍历的容器结构
