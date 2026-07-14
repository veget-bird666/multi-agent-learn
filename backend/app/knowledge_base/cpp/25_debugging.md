# C++ 调试与测试

## 调试基础

调试是定位程序错误的过程。C++ 程序常见错误分为：

| 类型 | 示例 | 主要工具 |
|:---|:---|:---|
| 编译错误 | 语法、类型不匹配 | 编译器输出 |
| 链接错误 | 重复定义、未定义符号 | 链接器输出 |
| 运行时错误 | 崩溃、异常 | GDB、Sanitizer |
| 逻辑错误 | 结果不对 | 单元测试、日志 |
| 未定义行为 | 越界、数据竞争 | UBSan、TSan、代码审查 |

**防御式编程**：在代码中提前检测"不应发生"的条件，防止问题扩散。

## 编译选项

```bash
# 调试构建
g++ -g -O0 -Wall -Wextra -std=c++17 -o program program.cpp

# 发布构建
g++ -O2 -DNDEBUG -std=c++17 -o program program.cpp

# 更严格警告
g++ -g -O0 -Wall -Wextra -Wpedantic -Werror -std=c++17 -o program program.cpp
```

| 选项 | 作用 |
|:---|:---|
| `-g` | 生成调试符号（DWARF） |
| `-O0` | 关闭优化，便于单步、变量可见 |
| `-O2` / `-O3` | 发布优化（可能内联、重排，调试困难） |
| `-Wall -Wextra` | 开启常见警告 |
| `-Werror` | 警告视为错误 |
| `-DNDEBUG` | 禁用 assert |
| `-DDEBUG` | 自定义调试宏开关 |
| `-fsanitize=address` | AddressSanitizer |
| `-fsanitize=undefined` | UndefinedBehaviorSanitizer |
| `-fsanitize=thread` | ThreadSanitizer |

**建议**：开发阶段 `-g -O0 -Wall -Wextra`；发布前在 CI 中跑 Sanitizer 构建。

## GDB 调试器

### 启动与基本命令

```bash
g++ -g program.cpp -o program
gdb ./program
```

| 命令 | 缩写 | 功能 |
|:---|:---|:---|
| `run` | `r` | 运行程序 `run arg1 arg2` |
| `break` | `b` | 断点 `b main` `b file.cpp:42` |
| `continue` | `c` | 继续到下一断点 |
| `next` | `n` | 单步跳过（不进入函数） |
| `step` | `s` | 单步进入函数 |
| `finish` | | 运行到当前函数返回 |
| `print` | `p` | 打印变量 `p x` `p arr[5]` |
| `display` | | 每次停止自动显示 |
| `backtrace` | `bt` | 查看调用栈 |
| `frame` | `f` | 切换栈帧 `f 2` |
| `list` | `l` | 显示源代码 |
| `info locals` | | 当前帧局部变量 |
| `info breakpoints` | | 断点列表 |
| `watch` | | 监视变量变化 `watch x` |
| `delete` | `d` | 删除断点 |
| `quit` | `q` | 退出 |

### 条件断点

```gdb
break 20 if i == 5
watch x if x > 100
```

### 调试 core dump

```bash
ulimit -c unlimited          # Linux：允许生成 core
./program                    # 崩溃后生成 core
gdb ./program core
(gdb) backtrace
(gdb) frame 3
(gdb) print variable
```

Windows 可用 Visual Studio 打开 dump 文件分析。

### 调试优化代码

`-O2` 下变量可能被优化掉、行号偏移。调试时优先 `-O0`；若必须调试优化版，用 `-Og`（GCC）或 `-O1`。

## 断言

```cpp
#include <cassert>

void divide(int a, int b) {
    assert(b != 0 && "Division by zero");
    // ...
}
```

**原则**：
- 检查**内部不变量**（"绝不应发生"）
- **不要**用 assert 检查用户输入（应返回错误码或抛异常）
- `NDEBUG` 定义时 assert 被完全移除

```cpp
// C++17 自定义断言（Release 也可保留）
#include <iostream>
#define MY_ASSERT(cond, msg) \
    do { \
        if (!(cond)) { \
            std::cerr << "Assert failed: " << msg \
                      << " at " << __FILE__ << ":" << __LINE__ << "\n"; \
            std::abort(); \
        } \
    } while(0)
```

### 契约与 expect

C++ 标准库尚未完全统一契约检查；项目内可约定：
- 前置条件：函数入口 assert 或抛 `std::invalid_argument`
- 后置条件：返回前 assert

## 日志

```cpp
#ifdef DEBUG
#define LOG(msg) \
    std::cerr << "[DEBUG] " << __FILE__ << ":" << __LINE__ \
              << " " << msg << std::endl
#else
#define LOG(msg)
#endif

LOG("Processing item " << id);
```

**生产环境**推荐 spdlog、glog、Boost.Log 等库，支持级别、轮转、异步写入。

```cpp
// spdlog 示例
#include <spdlog/spdlog.h>
spdlog::info("User {} logged in", userId);
spdlog::set_level(spdlog::level::debug);
```

## Sanitizer 与 Valgrind

### AddressSanitizer（ASan）

```bash
g++ -fsanitize=address -g -O1 program.cpp -o program
./program
```

检测：堆缓冲区溢出、栈溢出、use-after-free、double-free、部分内存泄漏。

### UndefinedBehaviorSanitizer（UBSan）

```bash
g++ -fsanitize=undefined -g program.cpp -o program
```

检测：有符号溢出、空指针解引用、未对齐访问、无效枚举等。

### ThreadSanitizer（TSan）

```bash
g++ -fsanitize=thread -g program.cpp -o program
```

检测数据竞争。不能与 ASan 同时启用。

### LeakSanitizer

通常随 ASan 启用。也可单独关注泄漏报告。

### Valgrind（Linux，无 Sanitizer 时）

```bash
valgrind --leak-check=full --show-leak-kinds=all ./program
valgrind --tool=memcheck ./program
```

**输出解读**：

```
==12345== 40 bytes in 2 blocks are definitely lost
==12345==    at malloc
==12345==    by create_array (main.cpp:15)
```

`definitely lost` 确定泄漏；`still reachable` 可能为全局对象，需人工判断。

**对比**：Sanitizer 更快、与编译器集成好；Valgrind 无需重编译，但较慢。

## 单元测试

### 手动测试框架概念

```cpp
#include <iostream>
#include <cmath>

#define TEST(name) void name(); struct name##_runner { name##_runner() { name(); } } name##_instance; void name()
#define ASSERT_EQ(a, b) do { if ((a) != (b)) { std::cerr << "FAIL: " << #a << " != " << #b << "\n"; std::abort(); } } while(0)

TEST(test_add) {
    ASSERT_EQ(1 + 1, 2);
}

TEST(test_sqrt) {
    ASSERT_EQ(static_cast<int>(std::sqrt(16)), 4);
}

int main() {
    std::cout << "All tests passed\n";
    return 0;
}
```

### Google Test 示例

```cpp
#include <gtest/gtest.h>

TEST(MathTest, Add) {
    EXPECT_EQ(1 + 1, 2);
    ASSERT_NEAR(3.14, 3.14159, 0.01);
}

TEST(VectorTest, Size) {
    std::vector<int> v{1, 2, 3};
    EXPECT_EQ(v.size(), 3u);
}

int main(int argc, char** argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

### Catch2 风格（单头文件）

```cpp
#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>

TEST_CASE("Factorial", "[math]") {
    REQUIRE(factorial(0) == 1);
    REQUIRE(factorial(5) == 120);
}
```

### 测试实践

- 覆盖**边界条件**：空容器、0、最大值、nullptr
- **隔离**：每个测试独立，不依赖执行顺序
- **快速**：单元测试应秒级完成，便于频繁运行
- **CI 集成**：每次提交自动跑测试 + Sanitizer 构建

## 常见 Bug 类型

### 1. 内存错误

- 数组/容器越界
- use-after-free、double-free
- 内存泄漏
- 返回局部变量指针/引用

**工具**：ASan、Valgrind、智能指针 + RAII

### 2. 未定义行为

- 有符号整数溢出
- 空指针解引用
- 未初始化变量
- 数据竞争

**工具**：UBSan、TSan、编译器警告、`-Wuninitialized`

### 3. 逻辑错误

- off-by-one
- 错误边界条件
- 浮点直接 `==` 比较

**方法**：单元测试、表格驱动测试、代码审查

### 4. 异常安全

- 资源泄漏（非 RAII）
- 强异常保证破坏

**方法**：RAII、拷贝-交换惯用法、测试异常路径

## 调试技巧

### 二分定位

注释或禁用一半代码，确定 bug 在前半还是后半，逐步缩小范围。Git bisect 对回归 bug 特别有效：

```bash
git bisect start
git bisect bad          # 当前版本有 bug
git bisect good v1.0    # 旧版本正常
# 自动 checkout 中间提交，测试后标记 good/bad
git bisect reset
```

### 最小复现

剥离无关代码，构造 **Minimal Reproducible Example**，便于提问和修复。

### Rubber Duck Debugging

向他人（或假想对象）逐步解释代码，往往在解释过程中发现问题。

### 打印调试

```cpp
std::cerr << "DEBUG: x=" << x << " y=" << y << std::endl;
```

简单有效。发布前移除或用条件编译 / 日志级别控制。

### 对比正确实现

对算法类 bug，与已知正确实现或标准库行为对比。

## IDE 与可视化调试

Visual Studio、CLion、VS Code（CodeLLDB / C/C++ Debug）均支持：

- 断点、条件断点、日志断点
- 变量监视、表达式求值
- 内存查看、反汇编
- 多线程调试、线程栈切换
- 时间旅行调试（部分商业工具）

**Windows 用户**：Visual Studio 对 MSVC 调试体验最佳；MinGW 可用 GDB。

## 静态分析

| 工具 | 说明 |
|:---|:---|
| clang-tidy | 基于 AST 的检查与现代化建议 |
| cppcheck | 轻量级静态分析 |
| PVS-Studio / Coverity | 商业深度分析 |
| 编译器警告 | 第一道防线 |

```bash
clang-tidy program.cpp -- -std=c++17
cppcheck --enable=all program.cpp
```

## 性能分析（简要）

逻辑正确后，若性能不足：

```bash
# Linux perf
perf record ./program
perf report

# gprof（传统）
g++ -pg program.cpp -o program
./program
gprof program gmon.out
```

**原则**：先测量再优化，避免过早优化。

## 学习要点总结

1. 调试构建用 `-g -O0 -Wall -Wextra`，CI 中跑 Sanitizer
2. GDB 掌握 break、run、next、step、print、backtrace
3. `assert` 验证内部不变量，用户输入用正常错误处理
4. 单元测试覆盖核心逻辑和边界条件，集成到 CI
5. 内存问题优先 ASan/Valgrind，数据竞争用 TSan
6. 用最小复现、二分、日志系统化定位，而非盲目改代码
7. 静态分析与编译器警告是成本最低的预防手段
