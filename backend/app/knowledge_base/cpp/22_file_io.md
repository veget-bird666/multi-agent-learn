# C++ 文件 I/O

## 文件 I/O 概览

C++ 提供两套主要的文件操作方式：

| 方式 | 头文件 | 特点 |
|:---|:---|:---|
| **fstream 流** | `<fstream>` | 类型安全、与 iostream 一致、RAII |
| **C 风格 FILE\*** | `<cstdio>` | 与 C 库互操作、部分底层 API 需要 |
| **filesystem** | `<filesystem>`（C++17） | 路径、目录、元数据操作 |

**推荐**：日常读写优先 `std::ifstream` / `std::ofstream` / `std::fstream`；路径与目录操作用 `std::filesystem`。

## 文本文件 vs 二进制文件

| 特性 | 文本模式 | 二进制模式 |
|:---|:---|:---|
| 内容 | 可打印字符 | 任意字节 |
| 换行符 | 可能做 `\n` ↔ `\r\n` 转换（平台相关） | 不做转换 |
| 读写方式 | `<<`、`>>`、`getline` | `read` / `write` |
| 可移植性 | 换行符因平台而异 | 字节布局需自行设计 |
| 典型用途 | 配置、日志、CSV | 图片、序列化、数据库 |

```cpp
#include <fstream>

// 文本模式（默认）
std::ifstream textIn("data.txt");

// 二进制模式
std::ifstream binIn("data.bin", std::ios::binary);
```

**关键**：在 Windows 上，文本模式会对换行做转换；二进制模式不做任何转换。读写非文本数据务必加 `std::ios::binary`。

## fstream 基础

```cpp
#include <fstream>
#include <string>
#include <iostream>

// 写文件
std::ofstream out("output.txt");
if (!out.is_open()) {
    std::cerr << "Cannot open file for writing\n";
    return 1;
}
out << "Hello, File!" << std::endl;
out.close();   // 析构时也会自动关闭

// 读文件
std::ifstream in("output.txt");
if (!in.is_open()) {
    std::cerr << "Cannot open file for reading\n";
    return 1;
}

std::string line;
while (std::getline(in, line)) {
    std::cout << line << std::endl;
}
// in 析构时自动 close
```

**RAII 原则**：`fstream` 对象离开作用域时自动关闭文件，通常不需要显式 `close()`，除非要在同一作用域内重新打开。

## 打开模式

```cpp
std::ofstream out1("data.txt");                              // 写，截断（默认）
std::ofstream out2("data.txt", std::ios::app);               // 追加
std::ofstream out3("data.bin", std::ios::binary);            // 二进制写
std::fstream  fs("log.txt", std::ios::in | std::ios::out);   // 读写
std::fstream  fs2("new.txt", std::ios::out | std::ios::trunc); // 显式截断
std::fstream  fs3("rw.bin", std::ios::in | std::ios::out | std::ios::binary | std::ios::app);
```

| 模式 | 含义 |
|:---|:---|
| `in` | 读 |
| `out` | 写 |
| `app` | 追加（写位置总在末尾） |
| `binary` | 二进制（不做换行转换） |
| `trunc` | 打开时截断已有内容（写模式默认） |
| `ate` | 打开后立即 seek 到末尾 |

**组合**：用 `|` 连接多个标志，如 `std::ios::in | std::ios::binary`。

## 格式化读写

### 输出格式化

```cpp
#include <fstream>
#include <iomanip>

std::ofstream out("report.txt");
out << std::fixed << std::setprecision(2);
out << "Price: " << 3.14159 << "\n";   // Price: 3.14
out << std::setw(10) << 42 << "\n";    // 右对齐宽度 10
```

### 输入格式化

```cpp
std::ifstream in("data.txt");
int id;
double value;
std::string name;

// 按空白分隔读取
while (in >> id >> value >> name) {
    std::cout << id << " " << value << " " << name << "\n";
}
```

**陷阱**：`>>` 以空白（空格、Tab、换行）为分隔符，**无法一次读入含空格的一整行**。读整行用 `std::getline`。

```cpp
// 文件内容："Alice Smith 25"
std::string word;
in >> word;   // 只得到 "Alice"，不是整行

// 正确：读整行
std::string line;
std::getline(in, line);   // "Alice Smith 25"
```

### 混合使用 >> 与 getline

```cpp
// 先用 >> 读数字，再 getline 读剩余行
int n;
in >> n;
in.ignore(std::numeric_limits<std::streamsize>::max(), '\n');  // 丢弃行尾换行
std::getline(in, restOfLine);
```

## 二进制读写

```cpp
struct Record {
    int id;
    double value;
};

// 写入
std::ofstream out("data.bin", std::ios::binary);
Record r{1, 3.14};
out.write(reinterpret_cast<const char*>(&r), sizeof(r));

// 读取
std::ifstream in("data.bin", std::ios::binary);
Record r2{};
in.read(reinterpret_cast<char*>(&r2), sizeof(r2));

if (in.gcount() != sizeof(r2)) {
    std::cerr << "Incomplete read\n";
}
```

**跨平台注意**：
- **结构体 padding**：不同编译器/平台对齐可能不同
- **字节序**：大端/小端可能不一致
- **类型大小**：`int`、`double` 宽度因平台而异

**推荐**：复杂数据用 JSON、Protobuf、MessagePack 等序列化格式，而非直接 `write` 结构体。

### 读写容器与缓冲区

```cpp
std::vector<char> buffer(4096);
std::ifstream in("large.bin", std::ios::binary);
while (in.read(buffer.data(), buffer.size()) || in.gcount() > 0) {
    std::streamsize n = in.gcount();
    // 处理 buffer[0..n)
}
```

## 文件状态检查

流对象继承自 `std::ios_base`，有四种状态标志：

| 方法 | 含义 |
|:---|:---|
| `good()` | 一切正常 |
| `eof()` | 到达文件末尾 |
| `fail()` | 逻辑错误（格式不匹配、打开失败） |
| `bad()` | 严重错误（流损坏） |

```cpp
std::ifstream in("data.txt");

if (in.fail()) { /* 打开或操作失败 */ }
if (in.eof())  { /* 到达文件末尾 */ }
if (in.good()) { /* 一切正常 */ }

// 恢复流状态（fail 后可 clear 再试）
in.clear();
in.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
```

**常见误区**：不要用 `eof()` 作为循环条件——应在读取**之后**检查返回值：

```cpp
// 错误
while (!in.eof()) {
    std::getline(in, line);   // 最后一次可能重复处理
}

// 正确
while (std::getline(in, line)) {
    // 处理 line
}
if (in.bad()) {
    std::cerr << "Read error\n";
}
```

## 定位操作

```cpp
std::fstream fs("data.bin", std::ios::in | std::ios::out | std::ios::binary);

fs.seekg(0, std::ios::end);    // 输入位置移到末尾
auto size = fs.tellg();        // 获取当前读位置

fs.seekg(0, std::ios::beg);    // 回到开头
fs.seekp(100, std::ios::beg);   // 输出位置移到第 100 字节
```

| 函数 | 作用 |
|:---|:---|
| `seekg(pos, whence)` | 设置**读**位置 |
| `seekp(pos, whence)` | 设置**写**位置 |
| `tellg()` | 返回当前读位置 |
| `tellp()` | 返回当前写位置 |

**whence**：`std::ios::beg`（开头）、`std::ios::cur`（当前）、`std::ios::end`（末尾）。

**注意**：文本模式下 seek 行为可能因换行转换而不可靠；随机访问建议用二进制模式。

## filesystem（C++17）

```cpp
#include <filesystem>
#include <iostream>

namespace fs = std::filesystem;

void demoFilesystem() {
    fs::path p = "data/config.txt";

    if (fs::exists(p)) {
        std::cout << "Size: " << fs::file_size(p) << " bytes\n";
        std::cout << "Extension: " << p.extension() << "\n";
    }

    fs::create_directories("output/logs");   // 递归创建目录
    fs::copy_file("src.txt", "dst.txt", fs::copy_options::overwrite_existing);
    fs::rename("old.txt", "new.txt");
    fs::remove("temp.txt");
    fs::remove_all("output");   // 递归删除目录

    for (const auto& entry : fs::directory_iterator(".")) {
        std::cout << (entry.is_directory() ? "[DIR] " : "      ")
                  << entry.path().filename() << "\n";
    }

    // 递归遍历
    for (const auto& entry : fs::recursive_directory_iterator("project")) {
        if (entry.is_regular_file() && entry.path().extension() == ".cpp") {
            std::cout << entry.path() << "\n";
        }
    }
}
```

### path 拼接

```cpp
fs::path base = "/home/user";
fs::path full = base / "data" / "file.txt";   // 跨平台路径拼接

#ifdef _WIN32
    fs::path win = R"(C:\Users\data\file.txt)";
#else
    fs::path unix = "/home/user/data/file.txt";
#endif
```

避免硬编码 `\` 或 `/`，用 `fs::path` 的 `/` 运算符拼接。

## 缓冲与 flush

```cpp
std::ofstream out("log.txt");
out << "Important message";
out.flush();           // 强制写入磁盘
out << std::flush;     // 同上

// endl 会换行并 flush
out << "Line" << std::endl;

// 性能敏感：用 '\n' 代替 endl，减少 flush 次数
out << "Fast line\n";
```

**全缓冲 vs 行缓冲**：标准库实现细节因平台而异。日志、崩溃诊断等关键输出可主动 `flush()`。

## 实用模式

### RAII 文件管理

```cpp
void processFile(const std::string& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("Cannot open: " + path);
    }
    // 使用 in...
}   // 离开作用域自动 close
```

### 一次性读入整个文件

```cpp
#include <sstream>

std::string readWholeFile(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) throw std::runtime_error("Cannot open: " + path);

    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}
```

### 写入临时文件

```cpp
#include <filesystem>
namespace fs = std::filesystem;

fs::path tempPath = fs::temp_directory_path() / "myapp_temp.txt";
{
    std::ofstream out(tempPath);
    out << "temporary data\n";
}
fs::remove(tempPath);   // 用完后删除
```

### 逐行处理大文件

```cpp
void processLargeFile(const fs::path& path) {
    std::ifstream in(path);
    if (!in) return;

    std::string line;
    std::size_t lineNo = 0;
    while (std::getline(in, line)) {
        ++lineNo;
        // 处理每一行，内存占用恒定
    }
}
```

## 与 C stdio 互操作

```cpp
#include <cstdio>

FILE* fp = std::fopen("data.txt", "r");
if (fp) {
    char buf[256];
    while (std::fgets(buf, sizeof(buf), fp)) {
        std::cout << buf;
    }
    std::fclose(fp);
}
```

需要 `fileno`、`mmap` 等底层 API 时可能用到 C 接口；新代码仍优先 fstream。

## 常见错误

### 1. 不检查打开是否成功

```cpp
std::ifstream in("missing.txt");
std::string line;
std::getline(in, line);   // 失败，line 不变，且可能误以为成功
```

**修复**：`if (!in)` 或 `if (!in.is_open())` 检查。

### 2. 用 >> 读含空格的行

```cpp
std::string word;
in >> word;   // 只读到第一个空白
```

整行用 `std::getline(in, line)`。

### 3. 二进制文件未加 binary 标志

```cpp
std::ifstream in("image.png");   // Windows 上可能因 0x1A 提前 EOF
std::ifstream in2("image.png", std::ios::binary);   // 正确
```

### 4. 直接 write 结构体跨平台

不同编译器的 struct padding、字节序可能不同。应使用明确的序列化格式。

### 5. 路径硬编码

```cpp
std::ifstream in("C:\\data\\file.txt");   // 仅 Windows 有效
fs::path p = fs::path("data") / "file.txt";   // 跨平台
```

### 6. 混用 tellg/tellp 与文本模式 seek

文本模式下位置与字节偏移不一定一一对应，随机访问用二进制模式。

## 学习要点总结

1. 始终检查文件是否成功打开（`if (!stream)`）
2. 读整行用 `getline`，按字段格式化读用 `>>`
3. 二进制 I/O 必须加 `std::ios::binary`
4. 复杂数据序列化避免直接 write 结构体，注意 padding 与字节序
5. C++17 `filesystem` 处理路径拼接、目录遍历与元数据
6. 用 RAII（fstream 对象）管理文件生命周期，避免泄漏
7. 性能敏感场景用 `'\n'` 代替 `std::endl`，减少不必要的 flush
