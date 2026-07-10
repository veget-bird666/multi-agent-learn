# C++ 命名空间

## 为什么需要命名空间

大型项目中，不同模块可能定义同名符号：

```cpp
// 模块 A
class Buffer { /* ... */ };

// 模块 B
class Buffer { /* ... */ };   // 冲突！
```

C 语言用**前缀**（`lib_buffer_create`）或 `static` 限制链接域；C++ 用**命名空间**组织代码，避免名称冲突，支持逻辑分组。

```cpp
namespace graphics {
    class Buffer { /* GPU 缓冲 */ };
}

namespace network {
    class Buffer { /* 网络缓冲 */ };
}

graphics::Buffer gb;
network::Buffer nb;
```

## 定义与使用

```cpp
namespace MyProject {
    class Widget {
    public:
        void doWork();
    };

    void init();
    constexpr int VERSION = 1;
}

// 作用域解析运算符 ::
MyProject::Widget w;
MyProject::init();
```

**命名空间可跨多个翻译单元、多个头文件**：

```cpp
// file1.h
namespace lib { void foo(); }

// file2.h
namespace lib { void bar(); }   // 同一命名空间，合并
```

## using 声明与 using 指令

### using 声明：引入单个名称

```cpp
using MyProject::Widget;
Widget w;   // 等价于 MyProject::Widget w;
```

### using 指令：引入整个命名空间

```cpp
using namespace MyProject;
Widget w2;
init();
```

| | using 声明 | using 指令 |
|:---|:---|:---|
| 范围 | 单个名称 | 整个命名空间 |
| 冲突 | 明确，易追踪 | 可能引入大量同名符号 |
| 头文件中 | 谨慎使用 | **禁止**（尤其 `using namespace std`） |

**最佳实践**：
- `.cpp` 实现文件中可局部 `using`
- **头文件中禁止** `using namespace std;`，会污染所有 include 者
- 优先 `std::` 前缀或 using 声明单个名称

**原因示例**：

```cpp
// bad_header.h
using namespace std;
class vector { /* ... */ };   // include 者可能 vector 冲突

// user.cpp
#include "bad_header.h"
vector<int> v;   // 歧义：std::vector 还是 bad_header::vector？
```

## 嵌套命名空间

```cpp
namespace company {
namespace project {
namespace detail {

void internalHelper() {}

}  // detail
}  // project
}  // company

company::project::detail::internalHelper();
```

**C++17 简写**：

```cpp
namespace company::project::detail {
    void internalHelper();
}
```

**用途分层**：

| 层级 | 典型内容 |
|:---|:---|
| 顶层 | 项目/库名 |
| 中层 | 模块/子系统 |
| `detail` | 内部实现，不保证 API 稳定 |

## 匿名命名空间

```cpp
namespace {
    int internalVar = 42;   // 内部链接
    void helper() {}
}
```

等价于 C 的 `static` 全局变量/函数（**内部链接**，仅本翻译单元可见）。

```cpp
// C 风格
static int internalVar = 42;
static void helper() {}

// C++ 推荐
namespace {
    int internalVar = 42;
    void helper() {}
}
```

**与 static 区别**：匿名命名空间是 C++ 推荐方式；`static` 在 C++ 中仍有效但风格上更倾向匿名命名空间。

**用途**：`.cpp` 文件内的辅助函数/常量，避免与其他翻译单元符号冲突。

## inline 命名空间（C++11）

```cpp
namespace library {
inline namespace v2 {
    void func() { std::cout << "v2\n"; }
}
namespace v1 {
    void func() { std::cout << "v1\n"; }
}
}

library::func();        // 调用 v2（inline 版本是默认）
library::v2::func();    // 显式 v2
library::v1::func();    // 显式旧版本
```

**用途**：
- **版本控制**：默认使用最新 inline 版本
- **ABI 兼容**：旧代码可显式指定 `v1`

## 命名空间别名

```cpp
namespace very_long_project_name {
    void work();
    class Widget {};
}

namespace vpn = very_long_project_name;
vpn::work();
vpn::Widget w;
```

**C++14 起**也可别名模板：

```cpp
template<typename T>
using Vec = std::vector<T>;
```

## ADL（Argument-Dependent Lookup）

也称 **Koenig 查找**：函数调用时，除通常作用域外，还在**实参类型所属命名空间**中查找函数。

```cpp
namespace math {
    struct Vector { double x, y; };
    void print(const Vector& v) {
        std::cout << "(" << v.x << ", " << v.y << ")\n";
    }
}

math::Vector v{1, 2};
print(v);   // 找到 math::print，无需 math::print(v)
```

**ADL 规则要点**：
1. 普通查找 + 参数类型关联命名空间
2. 适用于函数名（含 operator）
3. 不适用于类名、变量名

### ADL 与 std 算法

```cpp
namespace my {
    struct Widget { int id; };
    void swap(Widget& a, Widget& b) {
        std::swap(a.id, b.id);
    }
}

my::Widget a{1}, b{2};
using std::swap;
swap(a, b);   // ADL 找到 my::swap
```

**最佳实践**：自定义类型若需参与 generic 代码，在**同一命名空间**提供 `swap`、`begin`/`end` 等。

### ADL 陷阱

```cpp
namespace A { struct X {}; void foo(X); }
namespace B { void foo(A::X); }

A::X x;
foo(x);   // 歧义！A 和 B 都有 foo(X)
```

**修复**：显式 `A::foo(x)` 或 `B::foo(x)`。

## std 命名空间

标准库所有符号在 `std` 中：

```cpp
std::vector<int> v;
std::cout << "Hello" << std::endl;
std::sort(v.begin(), v.end());
```

**禁止**向 `std` 添加：
- 新函数、变量、类型（未定义行为）
- **允许**：为标准库模板做**特化**（如 `std::hash<MyType>`）

```cpp
// 允许：hash 特化
namespace std {
template<>
struct hash<MyType> {
    size_t operator()(const MyType& t) const { return t.id; }
};
}

// 禁止：添加新函数
namespace std {
void myHelper();   // UB！
}
```

## 头文件组织示例

```cpp
// widget.h
#ifndef WIDGET_H
#define WIDGET_H

#include <string>

namespace myapp {

class Widget {
public:
    explicit Widget(const std::string& name);
    void doWork();
private:
    std::string name_;
};

void initializeLibrary();

}  // namespace myapp

#endif
```

```cpp
// widget.cpp
#include "widget.h"
#include <iostream>

namespace myapp {

Widget::Widget(const std::string& name) : name_(name) {}

void Widget::doWork() {
    std::cout << name_ << " working\n";
}

void initializeLibrary() { /* ... */ }

}  // namespace myapp
```

**规范**：
- 头文件用 include guard 或 `#pragma once`
- 命名空间在头文件末尾注释 `}  // namespace myapp`
- 不在头文件 `using namespace std`

## 未命名空间 vs 静态 vs 匿名 namespace

| 方式 | 链接性 | C++ 推荐 |
|:---|:---|:---|
| 全局 `static` 函数 | 内部 | 可用，老式 |
| 匿名 namespace | 内部 | **推荐** |
| 未命名 namespace 中的类 | 内部 | 推荐 |

## C 模块对比

| | C | C++ |
|:---|:---|:---|
| 避免符号冲突 | `static`、前缀命名 | namespace |
| 逻辑分组 | 目录/前缀 | namespace 嵌套 |
| 版本管理 | 手动后缀 `_v2` | inline namespace |
| 查找规则 | 简单 | ADL 扩展 |

C11 无 namespace；C++20 **Modules**（`import`）是更现代的替代，但 namespace 仍广泛使用。

## 常见错误与陷阱

### 1. 头文件 using namespace std

```cpp
// utils.h
using namespace std;   // 污染所有 include 者
```

**原因**：include 顺序不同可能导致不同编译结果；第三方库可能与 std 冲突。

### 2. 在 std 中特化禁止的类型

只能为标准库**明确允许**的模板特化（如 `hash`、`less`、`allocator`）。随意特化 `vector<MyType>` 是 UB。

### 3. 混淆 using 声明与 using 指令

```cpp
using std::cout;              // 安全：只引入 cout
using namespace std;          // 危险：引入数千符号
```

### 4. 忘记 ADL 导致找不到自定义 operator

```cpp
namespace geom {
    struct Point { int x, y; };
    bool operator==(const Point& a, const Point& b) {
        return a.x == b.x && a.y == b.y;
    }
}

geom::Point p1{1, 2}, p2{1, 2};
// 在 namespace geom 外：
// p1 == p2;   // OK，ADL 找到 geom::operator==
```

若 `operator==` 不在 `geom` 命名空间，ADL 找不到。

### 5. 多重定义与 ODR

命名空间不影响 ODR（One Definition Rule）：同一程序中，非 inline 函数/变量只能有一份定义。

```cpp
// a.cpp
namespace lib { int value = 1; }   // 定义

// b.cpp
namespace lib { int value = 2; }   // 链接错误：重复定义
```

**修复**：头文件声明，一个 .cpp 定义；或 `inline` 变量（C++17）。

### 6. 嵌套过深

```cpp
company::project::module::submodule::detail::helper();
```

**修复**：命名空间别名 `namespace cpmsd = company::project::module::submodule::detail;`

## 学习要点总结

1. 命名空间**组织代码、避免冲突**，是 C++ 大型项目的基础
2. 头文件**禁止** `using namespace`，尤其 `using namespace std`
3. **匿名命名空间**实现翻译单元内部链接，替代 C 的 static
4. C++17 `namespace A::B::C` 简化嵌套；**inline namespace** 做版本控制
5. **ADL** 使自定义类型能参与 `swap`、标准算法等泛型代码
6. 不能向 `std` 添加符号；允许的特化遵循标准规定
