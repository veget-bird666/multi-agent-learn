# C++ Lambda 与函数式编程

## Lambda：匿名函数对象

C 语言用**函数指针**实现回调（如 `qsort` 的比较函数），语法晦涩且无法携带状态。C++ Lambda 是编译器生成的**匿名函数对象**，可捕获外部变量，与 STL 算法天然配合。

```cpp
auto add = [](int a, int b) { return a + b; };
std::cout << add(3, 4) << std::endl;   // 7

// 完整语法
// [capture](parameters) specifiers -> return_type { body }
```

**与 C 函数指针对比**：

| 特性 | C 函数指针 | C++ Lambda |
|:---|:---|:---|
| 语法 | `int (*fp)(int,int)` | `[](int a, int b) { return a+b; }` |
| 捕获状态 | 不能（需全局/参数传递） | `[x, &y]` 捕获 |
| 内联 | 取决于优化 | 通常完全内联 |
| 模板/generic | 不支持 | C++14 泛型 Lambda |
| 类型 | 单一函数签名 | 每个 Lambda 唯一类型 |

## 捕获列表详解

```cpp
int x = 10, y = 20;

// 值捕获：拷贝一份，Lambda 内修改不影响外部
auto f1 = [x](int z) { return x + z; };
// x = 100;  // f1 内 x 仍为 10

// 引用捕获：别名外部变量，可修改
auto f2 = [&x](int z) { x += z; };

// 混合捕获
auto f3 = [x, &y]() { y = x + 1; };

// 默认捕获
auto f4 = [=]() { return x + y; };    // 值捕获所有用到的外部变量
auto f5 = [&]() { x = 100; };       // 引用捕获所有用到的

// C++14 广义捕获（init capture）
auto f6 = [ptr = std::make_unique<int>(42)]() {
    return *ptr;
};
auto f7 = [v = std::move(someString)]() { return v.size(); };
```

| 捕获 | 含义 | 生命周期注意 |
|:---|:---|:---|
| `[]` | 不捕获 | — |
| `[x]` | 值捕获 x | 拷贝独立 |
| `[&x]` | 引用捕获 x | x 必须存活 |
| `[=]` | 值捕获所有用到的 | 安全但可能拷贝开销 |
| `[&]` | 引用捕获所有用到的 | 危险，易悬空 |
| `[x=expr]` | 广义捕获，初始化新成员 | 可 move 进 Lambda |

### 捕获 this（成员函数中）

```cpp
class Widget {
    int value = 42;
public:
    auto getCallback() {
        // C++17 前：[this] 或 [=] 捕获 this 指针
        // C++17 起：[*this] 值捕获整个对象（拷贝）
        return [*this]() { return value; };
    }
};
```

**陷阱**：`[=]` 在成员函数中默认捕获 `this` 指针（非 `*this`），若对象已销毁则悬空。

## 与 STL 算法配合

```cpp
#include <algorithm>
#include <vector>

std::vector<int> v = {5, 2, 8, 1, 9};

// 排序
std::sort(v.begin(), v.end(), [](int a, int b) {
    return a > b;   // 降序
});

// 条件计数
int threshold = 5;
auto count = std::count_if(v.begin(), v.end(),
    [threshold](int x) { return x > threshold; });

// 变换
std::transform(v.begin(), v.end(), v.begin(),
    [](int x) { return x * 2; });

// 查找
auto it = std::find_if(v.begin(), v.end(),
    [](int x) { return x % 2 == 0; });
```

**C 对比**：等价于 `qsort` 的比较函数，但 Lambda 可内联且无函数指针间接调用开销。

## mutable Lambda

值捕获的变量默认是 `const`，不能修改：

```cpp
int n = 0;
auto counter = [n]() mutable { return ++n; };
counter();   // 1
counter();   // 2
// n 仍为 0，修改的是捕获的副本
```

`mutable` 允许修改值捕获的副本，但不影响外部变量。

## 泛型 Lambda（C++14）

```cpp
auto print = [](const auto& x) {
    std::cout << x << std::endl;
};

print(42);
print("hello");
print(3.14);
```

编译器为每个 `auto` 参数生成模板 `operator()`，等价于：

```cpp
// C++20 显式模板语法
auto print = []<typename T>(const T& x) {
    std::cout << x << std::endl;
};
```

## 立即调用 Lambda（IIFE）

```cpp
int result = [](int a, int b) {
    return a + b;
}(3, 4);   // 7

// 复杂初始化，限制作用域
const std::map<std::string, int> config = []() {
    std::map<std::string, int> m;
    m["timeout"] = 30;
    m["retries"] = 3;
    return m;
}();
```

**用途**：避免临时变量污染外层作用域；在 const 上下文做复杂初始化。

## Lambda 的底层实现

编译器将 Lambda 转换为**闭包类**：

```cpp
// 源码
int base = 10;
auto add = [base](int x) { return base + x; };

// 大致等价于
class __Lambda_1 {
    int base;   // 捕获的成员
public:
    __Lambda_1(int b) : base(b) {}
    int operator()(int x) const { return base + x; }
};
__Lambda_1 add(10);
```

**每个 Lambda 表达式有唯一类型**，不能直接用同一类型名声明（除非用 `auto` 或 `std::function`）。

## std::function：类型擦除包装

```cpp
#include <functional>

std::function<int(int, int)> op = [](int a, int b) { return a + b; };
op = [](int a, int b) { return a * b; };   // 可重新赋值不同 Lambda

std::vector<std::function<void()>> callbacks;
callbacks.push_back([]() { std::cout << "Hello\n"; });
```

| | Lambda (auto) | std::function |
|:---|:---|:---|
| 类型 | 唯一闭包类型 | 统一可调用签名 |
| 性能 | 通常零开销、可内联 | 可能堆分配、间接调用 |
| 存储 | 栈 / 内联 | 适合容器、回调参数 |
| 大小 | 编译期确定 | 固定大小（内部可能 new） |

**小对象优化（SBO）**：`std::function` 对小闭包可能内联存储，大闭包才堆分配。

## 函数对象（Functor）

Lambda 出现前的主流写法，仍可显式定义：

```cpp
struct Adder {
    int base;
    Adder(int b) : base(b) {}
    int operator()(int x) const { return base + x; }
};

Adder add10(10);
add10(5);   // 15

// 可用于算法
std::transform(v.begin(), v.end(), v.begin(), Adder(10));
```

**优势**：可复用、可命名、可含多个 `operator()` 重载。Lambda 适合一次性、局部逻辑。

## bind 与 ref（C++11，已不推荐）

```cpp
#include <functional>

auto f = std::bind([](int a, int b, int c) {
    return a + b + c;
}, 1, std::placeholders::_1, 2);

f(10);   // 1 + 10 + 2 = 13
```

**问题**：占位符 `_1` 可读性差，与 Lambda 混用易错。**C++14 起推荐 Lambda 替代 bind**：

```cpp
auto f = [a = 1, c = 2](int b) { return a + b + c; };
```

## 回调与异步模式

```cpp
#include <functional>
#include <thread>

void process(int data, std::function<void(int)> callback) {
    int result = data * 2;
    callback(result);
}

process(21, [](int r) {
    std::cout << "Result: " << r << std::endl;
});

// 异步示例
std::thread t([msg = std::string("done")]() {
    std::cout << msg << std::endl;
});
t.join();
```

**线程安全**：Lambda 按值捕获变量是线程安全的（各自拷贝）；引用捕获需确保被引对象在线程执行期间存活。

## 常见错误与陷阱

### 1. 返回引用捕获的 Lambda

```cpp
auto bad = [&]() -> int& {
    int x = 10;
    return x;   // 悬空引用！
};
```

**原因**：`x` 是局部变量，函数返回后销毁。**修复**：返回值类型或值捕获。

### 2. 默认引用捕获导致悬空

```cpp
std::function<void()> createCallback() {
    int x = 42;
    return [&]() { std::cout << x; };   // x 已销毁！
}

auto cb = createCallback();
cb();   // 未定义行为
```

**原因**：Lambda 按引用捕获局部变量，但 `std::function` 延长的是 Lambda 对象而非被捕获变量。**修复**：值捕获 `[x]` 或 `[=]`。

### 3. 循环中 Lambda 捕获引用

```cpp
std::vector<std::function<void()>> funcs;
for (int i = 0; i < 3; ++i) {
    funcs.push_back([&]() { std::cout << i; });   // 全部打印 3！
}
```

**原因**：捕获的是 `i` 的引用，循环结束时 `i == 3`。**修复**：`[i]` 值捕获，或 C++14 `[i = i]`。

### 4. 过度使用 std::function

性能关键路径（如每帧调用百万次）应使用 `auto` + 模板，避免类型擦除开销：

```cpp
// 慢：可能堆分配 + 间接调用
template<typename F>
void apply(std::function<void(int)> f, int x) { f(x); }

// 快：模板内联
template<typename F>
void apply(F&& f, int x) { f(x); }
```

### 5. mutable 与 const 混淆

值捕获默认 `const`，忘记 `mutable` 无法修改副本。**原因**：Lambda 的 `operator()` 默认 const。

## std::invoke 与成员函数指针

C++17 的 `std::invoke` 统一调用普通函数、成员函数、函数对象：

```cpp
#include <functional>

struct Calculator {
    int base = 10;
    int add(int x) const { return base + x; }
};

Calculator calc;
auto mem_fn = &Calculator::add;

// 直接调用成员函数指针较繁琐
(calc.*mem_fn)(5);                          // 15
std::invoke(mem_fn, calc, 5);              // 等价，更通用

// Lambda 捕获成员函数
auto callAdd = [&calc](int x) { return calc.add(x); };
```

**与 C 函数指针对比**：C 无法直接表示成员函数指针（需 `void*` + 手动传 `this`），C++ Lambda 可隐式捕获 `this` 调用成员。

## 函数式编程风格小结

| 模式 | C 实现 | C++ 现代实现 |
|:---|:---|:---|
| 映射 transform | 手写 for 循环 | `std::transform` + Lambda |
| 过滤 filter | 手写 + 新数组 | `copy_if` 或 ranges `filter` |
| 归约 reduce | 手写累加 | `accumulate` / `reduce` |
| 排序 | `qsort` + 函数指针 | `std::sort` + Lambda |
| 回调 | 函数指针参数 | Lambda / `std::function` |

**原则**：声明式（"做什么"）优于命令式（"怎么做"），但避免过度嵌套 Lambda 导致可读性下降——复杂逻辑应提取为命名函数或 functor。

## 学习要点总结

1. Lambda 是 STL 算法和回调的**首选**，语法简洁、可内联
2. **值捕获**安全但有拷贝；**引用捕获**需注意生命周期
3. C++14 **广义捕获** `[ptr = std::move(p)]` 可转移所有权到 Lambda
4. 优先 Lambda 而非 `std::bind`，可读性更好
5. 不要返回捕获局部变量引用的 Lambda；循环中用值捕获
6. 需要存储异构回调时用 `std::function`，性能敏感处用模板 + `auto`
7. `std::invoke` 统一各种可调用对象的调用方式
