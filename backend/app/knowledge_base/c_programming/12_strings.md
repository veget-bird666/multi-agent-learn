# C语言字符串处理

## 字符串的本质

C语言没有专门的字符串类型，字符串是**以空字符 `\0` 结尾的字符数组**。

```c
char str1[] = "Hello";       // 数组，6字节（含 '\0'），内容可修改
char *str2 = "Hello";        // 指针，指向字符串常量，内容不可修改
```

**关键区别**：

| 特性 | `char str[] = "Hello"` | `char *str = "Hello"` |
|:---|:---|:---|
| 存储位置 | 栈（局部）或数据段（全局） | 只读数据段（字符串常量区） |
| 可修改性 | 可修改 | 不可修改（未定义行为） |
| `sizeof` | 6（数组大小） | 8（指针大小） |
| 生命周期 | 跟随作用域 | 程序全程 |

```c
char str[] = "Hello";
str[0] = 'h';           // 合法

char *p = "Hello";
p[0] = 'h';             // 未定义行为！可能崩溃（段错误）
```

## 字符串常量与指针

### 字符串常量的存储

```c
char *p1 = "Hello";
char *p2 = "Hello";
// p1 和 p2 可能指向同一内存地址（编译器优化）
```

**修改字符串常量的危险**：

```c
char *p = "Hello";
p[0] = 'h';   // 尝试修改只读内存
```

现代操作系统将字符串常量放在只读页，修改会触发**段错误（Segmentation Fault）**。

### 字符串数组

```c
// 指针数组（字符串常量）
char *names[] = {"Alice", "Bob", "Charlie"};
// names[0] 指向 "Alice"，不可修改

// 二维字符数组（可修改副本）
char names2[][10] = {"Alice", "Bob", "Charlie"};
// names2[0] 是包含 "Alice\0" 的数组，可以修改
```

## 标准字符串函数

### strlen

```c
size_t strlen(const char *s);
```

计算字符串长度（不包括 `\0`）：

```c
char str[] = "Hello";
size_t len = strlen(str);   // 5

// 注意：strlen 时间复杂度 O(n)，频繁使用考虑缓存
```

### strcpy 与 strncpy

```c
char dest[20];
strcpy(dest, "Hello");        // 复制包括 '\0'，不检查目标大小！

// 安全版本
strncpy(dest, "Hello", sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0';   // 确保终止！strncpy 不会自动加 '\0' 如果源更长
```

**strncpy 的陷阱**：

```c
char dest[5];
strncpy(dest, "Hello, World!", sizeof(dest));
// dest 内容为 "Hell"，没有 '\0'！
// 如果后续用 strlen(dest)，会越界读取直到找到 '\0'
```

### strcat 与 strncat

```c
char dest[20] = "Hello";
strcat(dest, " World");       // 不检查溢出！

// 安全版本
strncat(dest, " World", sizeof(dest) - strlen(dest) - 1);
```

### strcmp

```c
int strcmp(const char *s1, const char *s2);
```

返回值：
- `< 0`：s1 < s2（字典序）
- `== 0`：s1 == s2
- `> 0`：s1 > s2

```c
if (strcmp(str1, str2) == 0) {   // 正确：比较内容
    printf("相等\n");
}

// 常见错误
if (str1 == str2) { }            // 比较的是指针地址，不是内容！
```

### strchr, strstr

```c
char *strchr(const char *s, int c);     // 查找字符
char *strstr(const char *haystack, const char *needle);  // 查找子串

char str[] = "Hello, World!";
char *p = strchr(str, 'W');     // p 指向 "World!"
char *q = strstr(str, "World"); // q 指向 "World!"
```

### strtok（字符串分割）

```c
char str[] = "Hello,World,C";
char *token = strtok(str, ",");   // 第一次调用
while (token != NULL) {
    printf("%s\n", token);
    token = strtok(NULL, ",");    // 后续调用传 NULL
}
```

**strtok 的问题**：
1. **修改原字符串**：将分隔符替换为 `\0`
2. **非线程安全**：使用静态变量保存状态
3. **不能嵌套使用**：因为只有一个状态

**线程安全版本**：`strtok_r`（POSIX）或 `strtok_s`（C11）

```c
char *saveptr;
char *token = strtok_r(str, ",", &saveptr);
```

## 字符串与数字转换

### 字符串转整数

```c
int atoi(const char *str);           // 简单但不安全，溢出时行为未定义
long atol(const char *str);
double atof(const char *str);

// 安全版本
char *endptr;
long val = strtol("12345", &endptr, 10);   // 10进制
if (*endptr != '\0') {
    printf("转换不完整，剩余: %s\n", endptr);
}

// 检查溢出
errno = 0;
long val = strtol("99999999999999999999", &endptr, 10);
if (errno == ERANGE) {
    printf("溢出！\n");
}
```

### 数字转字符串

```c
char buffer[50];
sprintf(buffer, "%d", 12345);          // 不安全，可能溢出
snprintf(buffer, sizeof(buffer), "%d", 12345);  // 安全版本
```

## 宽字符与多字节

### 多字节字符（UTF-8）

```c
char utf8[] = "中文字符串";   // UTF-8 编码，每个中文字符占 3 字节
printf("%zu\n", strlen(utf8));  // 输出字节数，不是字符数！
```

### 宽字符（wchar_t）

```c
#include <wchar.h>

wchar_t wstr[] = L"中文";     // 宽字符字符串
printf("%zu\n", wcslen(wstr));  // 字符数

// 多字节与宽字符转换
char mbs[100];
wcstombs(mbs, wstr, sizeof(mbs));
```

## 安全字符串处理

### 使用安全函数

| 不安全 | 安全替代 |
|:---|:---|
| `strcpy` | `strncpy` / `strlcpy`（BSD） |
| `strcat` | `strncat` / `strlcat`（BSD） |
| `sprintf` | `snprintf` |
| `gets` | `fgets`（永远不要用 gets！） |
| `strlen` | 已安全，但注意 O(n) 复杂度 |

### 自定义安全复制

```c
// 安全的字符串复制
size_t safe_strcpy(char *dest, const char *src, size_t size) {
    if (size == 0) return 0;

    size_t i;
    for (i = 0; i < size - 1 && src[i] != '\0'; i++) {
        dest[i] = src[i];
    }
    dest[i] = '\0';

    return i;   // 返回复制的字符数
}
```

## 常见错误

### 1. 缓冲区溢出

```c
char buf[10];
strcpy(buf, "Hello, World!");   // 溢出！写入 14 字节到 10 字节空间
```

### 2. 缺少终止符

```c
char buf[5] = {'H', 'e', 'l', 'l', 'o'};   // 没有 '\0'！
printf("%s\n", buf);   // 越界读取直到找到 '\0'
```

### 3. 返回局部数组

```c
char *get_string(void) {
    char buf[] = "Hello";   // 局部数组
    return buf;              // 返回已失效的地址！
}
```

### 4. 忘记字符串需要 `\0`

```c
char buf[5];
memcpy(buf, "Hello", 5);    // 复制了 5 字节，但没有 '\0'
printf("%s", buf);           // 越界读取
```

## 学习要点总结

1. C字符串是以 `\0` 结尾的字符数组，`char[]` 可修改，`char*` 指向常量不可修改
2. 字符串函数大多不安全，优先使用带 `n` 的版本（strncpy、snprintf 等）
3. `strncpy` 不会保证加 `\0`，需要手动处理
4. `strcmp` 比较内容，`==` 比较地址
5. 永远不要使用 `gets`，总是使用 `fgets`
