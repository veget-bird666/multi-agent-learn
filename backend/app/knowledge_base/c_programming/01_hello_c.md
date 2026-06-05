# C语言环境搭建与第一个程序

## 从源代码到可执行文件

C语言是**编译型语言**，代码不能直接运行，必须经过编译器的翻译。理解这个过程对排查错误至关重要。

### 编译的四个阶段

```
hello.c (源代码)
    ↓
[预处理器 cpp] → 处理 #include, #define 等宏，生成 .i 文件
    ↓
[编译器 cc1] → 将C代码翻译成汇编语言，生成 .s 文件
    ↓
[汇编器 as] → 将汇编翻译成机器码，生成 .o 目标文件
    ↓
[链接器 ld] → 合并多个目标文件和库，生成可执行文件 a.out/hello.exe
```

你可以用 GCC 观察每个阶段：

```bash
gcc -E hello.c -o hello.i    # 仅预处理
gcc -S hello.i -o hello.s    # 仅编译到汇编
gcc -c hello.s -o hello.o    # 仅汇编到目标文件
gcc hello.o -o hello         # 链接生成可执行文件
```

### 为什么需要链接器？

你的 `printf` 函数并不是你写的，它存在于 C标准库 (libc) 中。链接器负责：
- **符号解析**：找到 `printf` 在库中的具体位置
- **重定位**：调整地址，因为每个目标文件都假设自己从地址0开始

## 第一个程序的深度解析

```c
#include <stdio.h>

int main(void) {
    printf("Hello, World!\n");
    return 0;
}
```

### 逐行剖析

**`#include <stdio.h>`**
- 这是**预处理指令**，不是C语句，不需要分号
- `<>` 表示在系统头文件目录查找（如 `/usr/include`）
- `""` 表示先在当前目录查找，再去系统目录
- `stdio.h` 中声明了 `printf` 的函数原型，没有它编译器会警告 "implicit declaration"

**`int main(void)`**
- `main` 是程序的唯一入口点，操作系统从这里开始执行
- 返回 `int` 是给操作系统看的：0 表示成功，非0表示各种错误码
- `void` 明确表示不接受参数（在C中 `int main()` 表示参数未指定，不是无参数）

**`return 0;`**
- 在 `main` 函数中，如果省略 `return`，C99标准会自动返回0（但不建议依赖此特性）

### 程序在内存中的布局

当程序运行时，操作系统会分配虚拟内存空间：

```
高地址
┌─────────────────┐
│    栈区 (Stack)  │ ← 局部变量、函数参数，向下增长
│                 │
├─────────────────┤
│    堆区 (Heap)   │ ← malloc 分配的内存，向上增长
│                 │
├─────────────────┤
│   数据段 (Data)  │ ← 全局变量、静态变量
│   - 已初始化     │
│   - 未初始化(BSS)│
├─────────────────┤
│  代码段 (Text)   │ ← 编译后的机器指令，只读
└─────────────────┘
低地址
```

## 开发环境搭建

### Linux/macOS (推荐)

```bash
# 检查是否已安装 GCC
gcc --version

# 编译并运行
gcc hello.c -o hello -Wall -Wextra -std=c11
./hello
```

编译选项说明：
- `-Wall`：开启所有常见警告（Write All）
- `-Wextra`：开启额外警告
- `-std=c11`：使用 C11 标准（2011年发布）
- `-g`：生成调试信息，供 GDB 使用
- `-O2`：优化级别2，平衡编译时间和运行性能

### 推荐的编译命令模板

```bash
gcc program.c -o program -Wall -Wextra -Werror -std=c11 -g -O0
```

- `-Werror`：将警告视为错误，强制写出干净代码
- `-O0`：关闭优化，调试时变量值不会被优化掉

## 常见错误与排查

### 1. 隐式函数声明

```c
int main(void) {
    printf("Hello");  // 忘记 #include <stdio.h>
    return 0;
}
```
**错误**：编译器假设 `printf` 返回 `int`，参数未知。在64位系统上如果实际返回 `void*` 会导致崩溃。

### 2. 忘记换行符

```c
printf("Hello");
```
输出不会立即显示！因为标准输出是**行缓冲**，遇到 `\n` 或缓冲区满才会刷新。解决：

```c
printf("Hello\n");
// 或
printf("Hello");
fflush(stdout);  // 强制刷新缓冲区
```

### 3. main 的返回值被忽略

虽然可以写 `void main()`，但这是**非标准**的，某些编译器会拒绝。始终使用 `int main(void)` 或 `int main(int argc, char *argv[])`。

## 学习要点总结

1. C程序必须经过预处理、编译、汇编、链接四个阶段
2. `#include` 是文本替换，不是模块导入
3. `main` 的返回值是给操作系统的状态码
4. 内存分为栈、堆、数据段、代码段四个区域
5. 始终使用 `-Wall -Wextra` 编译，把警告当错误处理
