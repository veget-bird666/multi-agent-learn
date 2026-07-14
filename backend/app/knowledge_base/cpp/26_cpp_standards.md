# C++ 标准版本与现代特性

## 标准版本概览

C++ 标准由 ISO 委员会制定，约每 3 年发布一版：

| 标准 | 年份 | `__cplusplus` | 主要特性 |
|:---|:---|:---|:---|
| C++98/03 | 1998/2003 | 199711L | STL、模板、异常、RAII |
| C++11 | 2011 | 201103L | auto、Lambda、智能指针、移动语义、线程 |
| C++14 | 2014 | 201402L | 泛型 Lambda、make_unique、数字分隔符 |
| C++17 | 2017 | 201703L | structured binding、optional、filesystem、variant |
| C++20 | 2020 | 202002L | concepts、ranges、coroutines、modules、format |
| C++23 | 2023 | 202302L | expected、print、更多 ranges、deducing this |

```bash
g++ -std=c++17 program.cpp
clang++ -std=c++20 program.cpp
cl /std:c++17 program.cpp    # MSVC
```

**推荐入门标准**：**C++17**（特性丰富、编译器支持广泛、生态成熟）。

## 编译器与标准支持

| 编译器 | C++17 | C++20 | C++23 |
|:---|:---|:---|:---|
| GCC 11+ | 完整 | 大部分 | 部分 |
| Clang 14+ | 完整 | 大部分 | 部分 |
| MSVC 2019 16.11+ | 完整 | 大部分 | 部分 |

查阅 [cppreference](https://en.cppreference.com/) 和 [compiler support](https://en.cppreference.com/w/cpp/compiler_support) 确认特定特性。

### 特性测试宏

C++20 起 `<version>` 提供 `__cpp_*` 宏：

```cpp
#include <version>

#if __cpp_lib_ranges >= 201911L
    #include <ranges>
#endif

#if __cpp_concepts >= 201907L
    // 使用 concepts
#endif
```

也可检测 `__cplusplus`：

```cpp
#if __cplusplus >= 202002L
    // C++20 及以上
#endif
```

## C++98/03 基础（回顾）

- STL 容器与算法
- 模板与特化
- 异常处理
- 命名空间
- RAII 与 auto_ptr（C++11 前智能指针）

**现状**：新代码不应以 C++03 为目标，但维护遗留代码时仍需了解。

## C++11 核心特性

C++11 是**现代化分水岭**，几乎所有现代 C++ 代码都假设至少 C++11。

```cpp
// auto 与 decltype
auto x = 42;
decltype(x) y = 10;

// 范围 for
for (const auto& item : container) { }

// Lambda
auto f = [](int x) { return x * 2; };

// 智能指针
auto p = std::make_unique<int>(42);
auto sp = std::make_shared<int>(42);

// 移动语义
std::vector<int> v2 = std::move(v1);

// nullptr
int* p = nullptr;

// 统一初始化
std::vector<int> v{1, 2, 3};

// enum class
enum class Color { Red, Green, Blue };

// override / final
void func() override;
class Final final {};

// 线程库
std::thread t([]{ });

// 右值引用、完美转发
// 可变参数模板
// std::function, std::bind
// constexpr（初版）
// static_assert
```

## C++14 特性

```cpp
// 泛型 Lambda
auto print = [](const auto& x) { std::cout << x; };

// make_unique
auto p = std::make_unique<Foo>();

// 二进制字面量、数字分隔符
auto b = 0b1010;
auto n = 1'000'000;

// constexpr 增强（可含循环）
constexpr int factorial(int n) {
    int r = 1;
    for (int i = 1; i <= n; ++i) r *= i;
    return r;
}

// 返回类型推导
auto foo() { return 42; }

// std::exchange, std::integer_sequence
```

## C++17 特性

```cpp
// structured binding
auto [key, value] = *map.begin();
std::pair p{1, 2.0};
auto [a, b] = p;

// if/switch 初始化
if (auto it = map.find(k); it != map.end()) { }

// std::optional
std::optional<int> find(int x);

// std::variant
std::variant<int, double, std::string> v;

// std::string_view
void process(std::string_view sv);

// filesystem
namespace fs = std::filesystem;

// 折叠表达式
template<typename... Args>
auto sum(Args... args) { return (args + ...); }

// inline 变量
inline constexpr double pi = 3.14159;

// 并行算法（execution::par）
// std::any, std::shared_mutex
```

## C++20 特性

```cpp
// concepts
template<std::integral T>
T add(T a, T b) { return a + b; }

// ranges
#include <ranges>
auto evens = v | std::views::filter([](int x){ return x % 2 == 0; });

// 三路比较 <=>
auto operator<=>(const Point&) const = default;

// coroutines
// co_await, co_yield, co_return

// modules
// export module foo; import bar;

// format
#include <format>
std::format("Hello, {}!", name);

// jthread, stop_token
std::jthread t([]{ });

// span
std::span<int> view(arr);

// consteval, constinit
// bit_cast
// 指定初始化 designated initializers
```

## C++23 特性（精选）

```cpp
// std::expected
std::expected<int, std::string> divide(int a, int b);

// std::print / println
#include <print>
std::print("Hello, {}!\n", name);

// std::generator（协程）
// std::flat_map, std::flat_set
// deducing this（显式对象参数）
// if consteval
// 更多 ranges 与 constexpr 增强
```

C++23 编译器支持仍在完善，使用前确认目标平台。

## 如何选择标准

```
学习 / 新项目     → C++17 或 C++20
维护旧代码        → 匹配项目已有标准
嵌入式 / 受限环境  → C++11/14 或厂商子集
竞赛 / 在线判题   → 通常 C++17 或 C++20（看平台）
```

**CMake 示例**：

```cmake
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)   # 禁用 gnu++17，使用严格 iso c++17
```

## ABI 与兼容性

### 源代码兼容 vs ABI 兼容

- **源代码兼容**：重新编译即可（如 C++14 → C++17 多数情况）
- **ABI 兼容**：已编译库无需重编即可链接（更严格）

**跨库边界注意**：
- 不同编译器、不同标准版本编译的库混链可能出问题
- 不要在 DLL 接口中传递 STL 容器（布局因版本而异）
- 接口用 C ABI 或稳定的 POD / 自定义协议

### 混合编译

主项目 C++17，静态链接 C++11 编译的库——通常可行，但需统一运行时（如 libstdc++ 版本）。

## 从旧标准迁移

### C++03 → C++11

- `NULL` → `nullptr`
- `typedef` → `using`
- 裸 `new/delete` → 智能指针
- 手写循环 → 算法 + Lambda
- `auto_ptr` → `unique_ptr`

### C++11 → C++17

- 引入 `optional`、`string_view`、`filesystem`
- structured binding 简化多返回值
- 考虑 `if` 初始化减少作用域

### 渐进策略

1. 启用更高 `-std`，修复编译错误
2. 开启更多警告（`-Wall -Wextra`）
3. 新代码用新特性，旧代码逐步重构
4. 用 clang-tidy 的 `modernize-*` 检查

## 现代 C++ 风格要点

1. **RAII** 管理资源，智能指针替代裸 new/delete
2. **STL 算法** 替代手写循环
3. **const 正确性** 和 **constexpr** 编译期计算
4. **auto** 推断复杂类型，简单类型可显式写出
5. **范围 for** 遍历容器
6. **enum class** 替代传统 enum
7. 避免 C 风格 cast，用 `static_cast` 等
8. **值语义** 优先，必要时才用指针/引用

## 常见错误

### 1. 混用标准特性与编译选项

```cpp
std::optional<int> x;   // 需要 C++17
// 编译：g++ program.cpp   ← 默认可能是 C++14，报错
// 正确：g++ -std=c++17 program.cpp
```

### 2. 盲目追新

项目团队、目标平台、第三方库不支持 C++20 时强行使用 modules，增加构建复杂度。

### 3. 忽视 ABI 兼容

插件/DLL 接口传递 `std::string`、`std::vector` 导致跨版本崩溃。

### 4. 假设 __cplusplus 总被正确设置

部分编译器需特定标志才更新 `__cplusplus`（如 GCC 旧版需 `-std=c++17` 且非 `-pedantic` 扩展问题）。用 `#if __cplusplus` 时配合特性测试宏更可靠。

### 5. 在线资源版本混乱

教程写 C++11，文档写 C++20，复制代码时未确认 `-std` 与头文件。

## 学习资源

- [cppreference.com](https://en.cppreference.com/) — 权威参考
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/) — 最佳实践
- *Effective Modern C++*（Scott Meyers）— C++11/14
- *A Tour of C++*（Bjarne Stroustrup）— 概览

## 学习要点总结

1. 推荐从 **C++17** 入门，掌握 auto、Lambda、智能指针、optional、filesystem
2. C++11 是现代化分水岭：移动语义、智能指针、线程、Lambda
3. C++20 的 concepts 和 ranges 进一步改善泛型与算法表达
4. 编译时指定 `-std=c++XX`，CMake 中 `CMAKE_CXX_STANDARD_REQUIRED ON`
5. 跨库/DLL 边界注意 ABI，接口避免 STL 容器
6. 用 `<version>` 特性测试宏做条件编译
7. 有效 C++ = RAII + STL + 类型安全，而非"C 风格 C++"
