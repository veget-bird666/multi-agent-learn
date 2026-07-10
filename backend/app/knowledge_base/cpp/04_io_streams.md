# C++ 输入输出流

## I/O 流的本质

C++ 标准库用**流（Stream）**抽象输入输出：数据像水流一样在"数据源/目的地"与"程序"之间单向流动。这与 C 的 `printf`/`scanf` 有根本不同——C 是**格式化函数 + 可变参数**，C++ 是**类型安全的运算符重载 + 状态机**。

```
数据源（键盘/文件/字符串） → [istream 输入流] → 程序
程序 → [ostream 输出流] → 目的地（屏幕/文件/字符串）
```

### C vs C++ I/O 对比

| 特性 | C (`printf`/`scanf`) | C++ (`iostream`) |
|:---|:---|:---|
| 类型安全 | 否，格式串 `%d` 必须与类型匹配 | 是，编译期检查 `<<`/`>>` |
| 性能 | 通常更快（尤其关闭同步后） | 默认略慢（locale、同步开销） |
| 扩展性 | 不可为用户类型扩展 | 可重载 `operator<<`/`>>` |
| 缓冲 | stdout 行缓冲，stderr 无缓冲 | cout 可缓冲，cerr 通常无缓冲 |
| 错误处理 | 返回读取/写入个数 | 流状态位 fail/eof/bad |
| 国际化 | 有限 | locale 支持更好 |

**建议**：新 C++ 代码优先 `iostream` 或 C++20 `std::format`；与 C 库交互或极致性能场景可用 `printf`。

## 标准流对象

| 对象 | 类型 | 含义 | 对应 C |
|:---|:---|:---|:---|
| `std::cin` | `istream` | 标准输入（键盘） | `stdin` |
| `std::cout` | `ostream` | 标准输出（屏幕） | `stdout` |
| `std::cerr` | `ostream` | 标准错误（无缓冲） | `stderr` |
| `std::clog` | `ostream` | 标准日志（有缓冲） | 类似 stderr |

```cpp
#include <iostream>

int main() {
    int age;
    std::cout << "Enter age: ";
    std::cin >> age;
    std::cout << "You are " << age << " years old." << std::endl;
}
```

### 缓冲的深层理解

```
程序调用 cout << "Hello"
    ↓
写入 cout 的内部缓冲区（用户空间）
    ↓
缓冲区满 / endl / flush / 程序结束
    ↓
系统调用 write() 写入内核
    ↓
终端/文件显示
```

**原因**：减少系统调用次数。`std::endl` 换行并 **flush**；`'\n'` 只换行，可能延迟显示。

**与 C 对比**：`printf` 到 stdout 通常是行缓冲；`stderr`/`cerr` 无缓冲，错误信息立即输出。

### ios_base 与 C 流的同步

默认 `std::ios::sync_with_stdio(true)`，C++ 流与 C 的 `stdin`/`stdout` 同步，保证混用顺序一致，但有性能代价：

```cpp
std::ios::sync_with_stdio(false);  // 关闭同步，提升性能
std::cin.tie(nullptr);             // 解除 cin 在 cout 前自动 flush
```

**防御式编程**：纯 C++ I/O 项目可关闭同步；必须与 C 代码混用时保持默认。

## 输出流操作

### 基本输出与链式调用

```cpp
int x = 42;
double pi = 3.14159;
std::string name = "Alice";

std::cout << "x = " << x << ", pi = " << pi << std::endl;
std::cout << "Hello, " << name << "!" << std::endl;

// 链式本质：operator<< 返回 ostream&，支持连续 <<
std::cout << "Line1" << std::endl << "Line2" << std::endl;
```

**逐步分析**：
1. `"x = "` 是 `const char*`，有对应的 `operator<<(ostream&, const char*)`
2. `x` 是 `int`，有 `operator<<(ostream&, int)`
3. 每次返回 `cout` 引用，继续下一个 `<<`

### 格式化输出（iomanip）

```cpp
#include <iomanip>

double val = 3.14159265;

std::cout << std::fixed << std::setprecision(2) << val << std::endl;  // 3.14
std::cout << std::scientific << std::setprecision(4) << val << std::endl;

std::cout << std::setw(10) << std::setfill('0') << 42 << std::endl;  // 0000000042

std::cout << std::hex << std::showbase << 255 << std::endl;  // 0xff
std::cout << std::dec << 255 << std::endl;                   // 255

std::cout << std::boolalpha << true << std::endl;  // true（默认输出 1）
```

**注意**：`std::fixed`、`std::hex` 等是**持久状态**，会影响后续输出，除非 `std::defaultfloat` 等恢复。

### 输出到字符串

```cpp
#include <sstream>

std::ostringstream oss;
oss << "Value: " << 42;
std::string result = oss.str();   // "Value: 42"
```

## 输入流操作

### 基本输入

```cpp
int n;
double d;
std::string s;

std::cin >> n;       // 读取整数，跳过前导空白
std::cin >> d;       // 读取浮点数
std::cin >> s;       // 读取单词，遇空白（空格/换行/制表）停止
```

**与 scanf 对比**：`>>` 类型安全，但**不读入空格**；读整行需 `getline`。

### 读取整行

```cpp
std::string line;
std::getline(std::cin, line);   // 读取一整行（含空格），遇 `\n` 停止

// 混合使用时的经典陷阱
int n;
std::cin >> n;                  // 用户输入 "42" 后按回车，'\n' 留在缓冲区
std::cin.ignore();              // 忽略一个字符（通常是 '\n'）
std::getline(std::cin, line);   // 现在才能正确读下一行
```

**原因**：`>>` 不消费行尾的 `\n`，下一次 `getline` 会读到空行。

**防御式编程**：

```cpp
std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
// 忽略直到换行或 EOF 的所有字符
```

### 输入验证（防御式编程）

```cpp
#include <limits>

int n;
if (std::cin >> n) {
    std::cout << "Read: " << n << std::endl;
} else {
    std::cout << "Invalid input!" << std::endl;
    std::cin.clear();   // 清除 failbit
    std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
}
```

**与 C 对比**：`scanf` 返回成功匹配项数；C++ 用流状态 `fail()`、`good()` 判断。

## 流状态与错误处理

每个流维护状态标志：

| 状态 | 含义 |
|:---|:---|
| `goodbit` | 一切正常 |
| `eofbit` | 到达文件末尾 |
| `failbit` | 逻辑错误（如类型不匹配、格式错误） |
| `badbit` | 物理错误（如磁盘故障） |

```cpp
if (std::cin.fail()) { /* 输入失败 */ }
if (std::cin.eof())  { /* 到达末尾 */ }
if (std::cin.good()) { /* 可继续读写 */ }

// 恢复流（fail 后必须 clear 才能继续读）
std::cin.clear();
std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
```

**原因**：读取失败后流进入 fail 状态，后续操作被忽略，直到 `clear()`。

## 文件流

```cpp
#include <fstream>
#include <string>

// 写文件
std::ofstream out("output.txt");
if (!out.is_open()) {
    std::cerr << "Failed to open file!" << std::endl;
    return 1;
}
out << "Hello, File!" << std::endl;
out.close();   // 析构时也会自动关闭（RAII）

// 读文件
std::ifstream in("input.txt");
std::string line;
while (std::getline(in, line)) {
    std::cout << line << std::endl;
}

// 追加模式
std::ofstream append("log.txt", std::ios::app);
append << "New log entry" << std::endl;
```

**RAII 优势**：`std::ifstream`/`ofstream` 析构时自动关闭文件，异常路径也不会泄漏句柄。C 的 `fopen`/`fclose` 需手动配对。

### 二进制 I/O

```cpp
struct Record { int id; double value; };

std::ofstream out("data.bin", std::ios::binary);
Record r{1, 3.14};
out.write(reinterpret_cast<const char*>(&r), sizeof(r));

std::ifstream in("data.bin", std::ios::binary);
Record r2;
in.read(reinterpret_cast<char*>(&r2), sizeof(r2));
```

**警告**：直接 `write`/`read` 结构体不可移植（对齐、endian 因平台而异）。序列化应使用明确格式或库（如 Protocol Buffers）。

## stringstream

在**内存字符串**上模拟流，常用于格式化和解析：

```cpp
#include <sstream>

// 格式化
std::ostringstream oss;
oss << std::fixed << std::setprecision(2) << 3.14159;
std::string s = oss.str();   // "3.14"

// 解析
std::istringstream iss("42 3.14 hello");
int n; double d; std::string word;
iss >> n >> d >> word;   // n=42, d=3.14, word="hello"
```

## C++20 格式化库

```cpp
#include <format>

std::string msg = std::format("Hello, {}! You are {} years old.", name, age);
std::cout << std::format("{:.2f}", pi) << std::endl;   // 3.14
std::cout << std::format("{:08x}", 255) << std::endl; // 000000ff
```

**优势**：比 `iostream` 格式化更高效，比 `printf` 类型安全（编译期检查占位符与参数）。

## 为用户自定义类型重载流运算符

```cpp
struct Point { double x, y; };

std::ostream& operator<<(std::ostream& os, const Point& p) {
    return os << "(" << p.x << ", " << p.y << ")";
}

std::istream& operator>>(std::istream& is, Point& p) {
    char c;
    is >> c >> p.x >> c >> p.y >> c;   // 读取 "(x, y)" 格式
    return is;
}

Point p{1.0, 2.0};
std::cout << p << std::endl;   // (1, 2)
```

**设计原则**：
- `operator<<` / `operator>>` 通常实现为**非成员友元函数**，以便 `cout << obj` 对称
- 返回 `istream&`/`ostream&` 引用以支持链式调用
- 输入失败时设置流 fail 状态，不抛异常（与标准库行为一致）

**与 C 对比**：C 无法用 `printf` 直接输出自定义结构体，需手动拆解字段或使用第三方库。

## 文件打开模式

| 模式 | 含义 |
|:---|:---|
| 默认 | 输出截断（覆盖），输入只读 |
| `std::ios::app` | 追加写入 |
| `std::ios::binary` | 二进制模式（Windows 上禁用 `\r\n` 转换） |
| `std::ios::in` / `out` | 读写（`fstream`） |
| `std::ios::trunc` | 打开时截断文件 |

```cpp
std::fstream fs("data.txt", std::ios::in | std::ios::out | std::ios::app);
```

## 常见错误

### 1. >> 与 getline 混用未清缓冲区

见上文"读取整行"节。**原因**：行尾 `\n` 残留。

### 2. 不检查流状态

```cpp
std::cin >> n;   // 用户输入 "abc"，n 未定义，流 fail
// 继续使用 cin 而不 clear()
```

**原因**：fail 状态下后续提取被跳过。

### 3. 不检查文件是否打开

```cpp
std::ofstream out("readonly/file.txt");
out << "data";   // 静默失败！
```

**防御**：始终 `if (!out.is_open())` 或使用 C++17 `std::filesystem` 预检查。

### 4. endl 滥用导致性能问题

```cpp
for (int i = 0; i < 1000000; ++i) {
    std::cout << i << std::endl;   // 每次都 flush，极慢
}
// 改用 '\n'，循环外或关键点 flush
```

### 5. 混用 printf 与 cout 不关闭同步

可能导致输出顺序混乱或性能下降。

## 学习要点总结

1. C++ I/O 基于流，核心是 `cin`、`cout`、`cerr`，类型安全可扩展
2. `<<` 输出，`>>` 输入；读整行用 `getline`，注意与 `>>` 混用时的 `\n` 残留
3. `<iomanip>` 提供格式化；`ostringstream` 做字符串格式化
4. 文件用 `ifstream`/`ofstream`，RAII 自动关闭；始终检查 `is_open()`
5. 输入失败后需 `clear()` + `ignore()` 恢复流状态
6. 性能敏感场景考虑 `sync_with_stdio(false)` 和用 `'\n'` 代替 `endl`
7. C++20 起优先 `std::format` 做类型安全格式化
