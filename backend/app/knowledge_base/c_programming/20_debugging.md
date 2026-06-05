# C语言调试与性能分析

## 调试基础

### 防御式编程

在代码中提前检测错误，防止问题扩散：

```c
#include <assert.h>

void process_array(int *arr, int n) {
    assert(arr != NULL);    // 调试时检查，Release 模式下通常禁用
    assert(n > 0);

    for (int i = 0; i < n; i++) {
        // ...
    }
}
```

**assert 的使用原则**：
- 检查"不可能发生"的条件
- 不要用于检查用户输入（应该用错误处理）
- Release 版本用 `NDEBUG` 宏禁用：`gcc -DNDEBUG`

### 自定义断言

```c
#ifdef NDEBUG
    #define MY_ASSERT(expr) ((void)0)
#else
    #define MY_ASSERT(expr)         do {             if (!(expr)) {                 fprintf(stderr, "Assertion failed: %s, file %s, line %d\n",                         #expr, __FILE__, __LINE__);                 abort();             }         } while(0)
#endif
```

## GDB 调试器

### 基本命令

```bash
gcc -g program.c -o program    # -g 生成调试信息
gdb ./program                  # 启动 GDB
```

| 命令 | 缩写 | 功能 |
|:---|:---|:---|
| `run` | `r` | 运行程序 |
| `break` | `b` | 设置断点 `b main` `b 20` `b file.c:30` |
| `continue` | `c` | 继续运行 |
| `step` | `s` | 单步进入（进入函数） |
| `next` | `n` | 单步跳过（不进入函数） |
| `finish` | | 运行到当前函数返回 |
| `print` | `p` | 打印变量值 `p x` `p arr[5]` |
| `display` | | 每次停止时自动显示 |
| `backtrace` | `bt` | 查看调用栈 |
| `frame` | `f` | 切换到指定栈帧 `f 2` |
| `list` | `l` | 显示源代码 |
| `info` | | 查看信息 `info breakpoints` `info locals` |
| `watch` | | 监视变量变化 `watch x` |
| `delete` | `d` | 删除断点 |
| `quit` | `q` | 退出 GDB |

### 条件断点

```gdb
break 20 if i == 5          # 当 i == 5 时才中断
watch x if x > 100          # 当 x > 100 时监视
```

### 核心转储（Core Dump）

```bash
ulimit -c unlimited          # 允许生成 core 文件
./program                    # 崩溃后生成 core 文件
gdb ./program core           # 用 GDB 分析 core 文件
```

## Valgrind 内存检测

### 内存泄漏检测

```bash
valgrind --leak-check=full --show-leak-kinds=all ./program
```

**输出解读**：

```
==12345== HEAP SUMMARY:
==12345==     in use at exit: 40 bytes in 2 blocks
==12345==   total heap usage: 3 allocs, 1 frees, 120 bytes allocated
==12345== 
==12345== 40 bytes in 2 blocks are definitely lost
==12345==    at 0x4C2FB0F: malloc (vg_replace_malloc.c:299)
==12345==    by 0x1086B2: create_array (main.c:15)
==12345==    by 0x1086E5: main (main.c:25)
```

### 非法内存访问

```bash
valgrind --tool=memcheck --track-origins=yes ./program
```

检测：
- 使用未初始化的内存
- 读写已释放的内存
- 数组越界
- 内存泄漏

### 性能分析

```bash
valgrind --tool=callgrind ./program
callgrind_annotate callgrind.out.*
```

## 常见调试技巧

### 1. 二分法定位bug

```c
// 在可疑区域插入检查点
printf("DEBUG: Before loop, i=%d\n", i);
// ... 可疑代码 ...
printf("DEBUG: After loop, i=%d\n", i);
```

### 2. 打印调用栈

```c
#include <execinfo.h>

void print_backtrace(void) {
    void *buffer[100];
    int n = backtrace(buffer, 100);
    backtrace_symbols_fd(buffer, n, STDERR_FILENO);
}
```

### 3. 内存边界检查

```c
#ifdef DEBUG
    #define MALLOC(size) debug_malloc(size, __FILE__, __LINE__)
    #define FREE(ptr) debug_free(ptr, __FILE__, __LINE__)
#else
    #define MALLOC(size) malloc(size)
    #define FREE(ptr) free(ptr)
#endif
```

### 4. 运行时日志

```c
#define LOG_LEVEL_DEBUG 0
#define LOG_LEVEL_INFO  1
#define LOG_LEVEL_WARN  2
#define LOG_LEVEL_ERROR 3

int current_log_level = LOG_LEVEL_DEBUG;

#define LOG(level, fmt, ...)     do {         if (level >= current_log_level) {             fprintf(stderr, "[%s:%d] " fmt "\n",                     __FILE__, __LINE__, ##__VA_ARGS__);         }     } while(0)

LOG(LOG_LEVEL_DEBUG, "x = %d", x);
```

## 性能优化基础

### 编译器优化

```bash
gcc -O0 program.c    # 无优化，适合调试
gcc -O1 program.c    # 基本优化
gcc -O2 program.c    # 推荐：平衡编译时间和性能
gcc -O3 program.c    # 激进优化，可能增加代码体积
gcc -Os program.c    # 优化代码体积
```

### 性能分析工具

```bash
# gprof
gcc -pg program.c -o program
./program
gprof ./program gmon.out

# perf（Linux）
perf record ./program
perf report
```

### 缓存友好性

```c
// 缓存不友好（跳跃访问）
for (int j = 0; j < cols; j++) {
    for (int i = 0; i < rows; i++) {
        sum += matrix[i][j];   // 跳跃访问
    }
}

// 缓存友好（连续访问）
for (int i = 0; i < rows; i++) {
    for (int j = 0; j < cols; j++) {
        sum += matrix[i][j];   // 连续访问
    }
}
```

## 学习要点总结

1. 使用 `assert` 检查"不可能发生"的条件，Release 版本禁用
2. GDB 是强大的调试工具，掌握断点、单步、查看变量、调用栈
3. Valgrind 检测内存泄漏和非法访问，是C程序必备工具
4. 编译器优化级别 `-O2` 是常用选择，调试时用 `-O0 -g`
5. 注意缓存友好性，按行优先访问多维数组
