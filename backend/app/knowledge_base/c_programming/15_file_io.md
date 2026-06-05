# C语言文件操作

## 文件基本概念

### 文本文件 vs 二进制文件

| 特性 | 文本文件 | 二进制文件 |
|:---|:---|:---|
| 内容 | 可打印字符 | 任意字节 |
| 换行符 | `\n`（Unix）或 `\r\n`（Windows） | 无转换 |
| 读取方式 | `fgets`、`fscanf`、`fprintf` | `fread`、`fwrite` |
| 可移植性 | 换行符可能因平台而异 | 完全一致 |
| 用途 | 配置文件、日志、源代码 | 图片、音频、数据库、序列化数据 |

**关键区别**：在 Windows 上，以文本模式打开文件时，`\n` 会自动转换为 `\r\n`，反之亦然。二进制模式不做任何转换。

```c
// 文本模式
FILE *fp = fopen("data.txt", "r");   // 读取时 \r\n → \n
FILE *fp = fopen("data.txt", "w");   // 写入时 \n → \r\n

// 二进制模式
FILE *fp = fopen("data.bin", "rb");  // 不做任何转换
```

## 标准I/O函数

### fopen 与 fclose

```c
FILE *fopen(const char *filename, const char *mode);
int fclose(FILE *stream);
```

**打开模式**：

| 模式 | 含义 | 文件存在 | 文件不存在 |
|:---|:---|:---|:---|
| `"r"` | 只读 | 打开 | 失败 |
| `"w"` | 只写 | 清空 | 创建 |
| `"a"` | 追加写 | 追加 | 创建 |
| `"r+"` | 读写 | 打开 | 失败 |
| `"w+"` | 读写 | 清空 | 创建 |
| `"a+"` | 读写追加 | 追加 | 创建 |
| `"rb"` | 二进制只读 | 同上 | 同上 |

```c
FILE *fp = fopen("data.txt", "r");
if (fp == NULL) {
    perror("fopen failed");   // 输出：fopen failed: No such file or directory
    return 1;
}
// ...
fclose(fp);
```

### 字符读写

```c
int fgetc(FILE *stream);           // 读取一个字符
int fputc(int c, FILE *stream);    // 写入一个字符

// 复制文件
FILE *src = fopen("source.txt", "r");
FILE *dst = fopen("dest.txt", "w");
int c;
while ((c = fgetc(src)) != EOF) {
    fputc(c, dst);
}
fclose(src);
fclose(dst);
```

### 行读写

```c
char *fgets(char *s, int size, FILE *stream);   // 读取一行
int fputs(const char *s, FILE *stream);          // 写入字符串

char line[256];
while (fgets(line, sizeof(line), fp) != NULL) {
    printf("%s", line);   // fgets 保留换行符
}
```

**fgets 的特点**：
- 读取最多 `size-1` 个字符
- 遇到 `\n` 或 EOF 停止
- 保留 `\n`（如果存在）
- 总是以 `\0` 结尾

### 格式化读写

```c
int fprintf(FILE *stream, const char *format, ...);
int fscanf(FILE *stream, const char *format, ...);

// 写入
fprintf(fp, "Name: %s, Age: %d\n", "Alice", 25);

// 读取
char name[50];
int age;
fscanf(fp, "Name: %s, Age: %d", name, &age);
```

**fscanf 的陷阱**：

```c
// 文件内容："Alice 25"
char name[50];
int age;
fscanf(fp, "%s %d", name, &age);   // 正确

// 但如果文件是 "Alice Smith 25"
fscanf(fp, "%s %d", name, &age);   // name 得到 "Alice"，age 读取失败
```

### 二进制读写

```c
size_t fread(void *ptr, size_t size, size_t nmemb, FILE *stream);
size_t fwrite(const void *ptr, size_t size, size_t nmemb, FILE *stream);

// 写入结构体数组
struct Student students[10];
// 填充数据...
fwrite(students, sizeof(struct Student), 10, fp);

// 读取
struct Student loaded[10];
size_t n = fread(loaded, sizeof(struct Student), 10, fp);
if (n != 10) {
    if (feof(fp)) {
        printf("文件结束，只读取了 %zu 个\n", n);
    } else if (ferror(fp)) {
        printf("读取错误\n");
    }
}
```

**注意**：`fread` 返回成功读取的**元素个数**，不是字节数。

## 文件定位

### fseek 与 ftell

```c
int fseek(FILE *stream, long offset, int whence);
long ftell(FILE *stream);
void rewind(FILE *stream);
```

**whence**：
- `SEEK_SET`：从文件开头
- `SEEK_CUR`：从当前位置
- `SEEK_END`：从文件末尾

```c
// 获取文件大小
fseek(fp, 0, SEEK_END);
long size = ftell(fp);
rewind(fp);   // 回到开头

// 跳到第 100 个字节
fseek(fp, 100, SEEK_SET);

// 向前跳 50 个字节
fseek(fp, 50, SEEK_CUR);

// 从末尾向前 10 个字节
fseek(fp, -10, SEEK_END);
```

**注意**：`ftell` 返回 `long`，对于超过 2GB 的文件可能溢出。大文件用 `ftello`（返回 `off_t`）。

### 大文件支持

```c
#define _FILE_OFFSET_BITS 64   // 启用大文件支持
#include <stdio.h>

off_t size = ftello(fp);   // 可以处理超过 2GB 的文件
fseeko(fp, 10000000000LL, SEEK_SET);
```

## 错误处理

### feof 与 ferror

```c
int feof(FILE *stream);    // 检查是否到达文件末尾
int ferror(FILE *stream);  // 检查是否发生错误
void clearerr(FILE *stream); // 清除错误标志
```

**常见误区**：

```c
// 错误用法
while (!feof(fp)) {        // feof 在读取失败后才会设置！
    fgetc(fp);             // 最后一次会读取 EOF 并处理
}

// 正确用法
int c;
while ((c = fgetc(fp)) != EOF) {   // 直接检查返回值
    // 处理 c
}
if (ferror(fp)) {
    printf("读取错误\n");
}
```

## 缓冲区控制

### setvbuf

```c
int setvbuf(FILE *stream, char *buf, int mode, size_t size);
```

**mode**：
- `_IOFBF`：全缓冲
- `_IOLBF`：行缓冲
- `_IONBF`：无缓冲

```c
// 设置行缓冲
setvbuf(stdout, NULL, _IOLBF, 0);

// 禁用缓冲
setvbuf(fp, NULL, _IONBF, 0);

// 自定义缓冲区
static char buffer[4096];
setvbuf(fp, buffer, _IOFBF, sizeof(buffer));
```

## 临时文件

```c
FILE *tmpfile(void);                    // 创建临时文件，fclose 时自动删除
char *tmpnam(char *s);                   // 生成临时文件名（不安全，已废弃）
FILE *tmpfile(void);                     // 推荐

FILE *fp = tmpfile();
if (fp == NULL) {
    perror("tmpfile failed");
    return 1;
}
// 使用临时文件...
fclose(fp);   // 自动删除
```

## 文件锁（POSIX）

```c
#include <fcntl.h>

// 建议性锁
struct flock fl;
fl.l_type = F_WRLCK;    // 写锁
fl.l_whence = SEEK_SET;
fl.l_start = 0;
fl.l_len = 0;           // 锁定整个文件

int fd = fileno(fp);    // FILE* 转文件描述符
fcntl(fd, F_SETLK, &fl);   // 非阻塞加锁
```

## 常见错误

### 1. 忘记检查 fopen 返回值

```c
FILE *fp = fopen("data.txt", "r");
// 如果文件不存在，fp 为 NULL，后续操作崩溃
```

### 2. 二进制文件用文本模式打开

```c
FILE *fp = fopen("image.png", "r");   // 错误！应该用 "rb"
// 在 Windows 上，0x1A（EOF 字符）会被误认为文件结束
```

### 3. 忘记 fclose

```c
void process(void) {
    FILE *fp = fopen("data.txt", "r");
    // 处理...
    // 忘记 fclose！资源泄漏
}
```

### 4. 使用已关闭的文件

```c
fclose(fp);
fgetc(fp);   // 未定义行为！
```

### 5. fscanf 格式不匹配

```c
int x;
fscanf(fp, "%f", &x);   // 格式是 float，但变量是 int！
```

## 学习要点总结

1. 文本模式会做换行符转换，二进制模式不做任何转换
2. 始终检查 `fopen` 返回值，使用 `perror` 输出错误信息
3. `fread`/`fwrite` 操作的是元素个数，不是字节数
4. 不要用 `feof` 作为循环条件，直接检查读取函数的返回值
5. 大文件使用 `ftello`/`fseeko`，启用 `_FILE_OFFSET_BITS=64`
