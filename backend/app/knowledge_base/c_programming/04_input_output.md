# C语言输入输出

## 标准I/O流

C程序启动时自动打开三个标准流：

| 流 | 名称 | 默认设备 | 用途 |
|:---|:---|:---|:---|
| `stdin` | 标准输入 | 键盘 | 读取用户输入 |
| `stdout` | 标准输出 | 屏幕 | 正常输出 |
| `stderr` | 标准错误 | 屏幕 | 错误输出 |

**重要区别**：`stdout` 是**行缓冲**或**全缓冲**，`stderr` 是**无缓冲**。这意味着错误信息会立即输出，而普通输出可能延迟。

```c
fprintf(stdout, "普通信息");    // 可能不立即显示
fprintf(stderr, "错误信息");    // 立即显示
```

## printf 家族

### 格式字符串

```c
printf("格式控制字符串", 参数1, 参数2, ...);
```

格式说明符：`%[标志][宽度][.精度][长度修饰符]转换说明`

### 常用转换说明

| 说明符 | 类型 | 示例输出 |
|:---|:---|:---|
| `%d` 或 `%i` | int | 42 |
| `%u` | unsigned int | 42 |
| `%ld` | long | 42L |
| `%f` | double | 3.140000 |
| `%e` | 科学计数法 | 3.140000e+00 |
| `%g` | 自动选择 %f 或 %e | 3.14 |
| `%c` | char | A |
| `%s` | 字符串 | Hello |
| `%p` | 指针 | 0x7ffd5e8c3a4c |
| `%%` | 字面量 % | % |

### 标志与格式控制

```c
int num = 42;
printf("[%10d]\n", num);     // [        42]  右对齐，宽度10
printf("[%-10d]\n", num);    // [42        ]  左对齐
printf("[%010d]\n", num);    // [0000000042]  前导零
printf("[%+10d]\n", num);    // [       +42]  显示正号

float pi = 3.14159;
printf("[%.2f]\n", pi);       // [3.14]  精度2位小数
printf("[%8.2f]\n", pi);      // [    3.14]  宽度8，精度2
```

### 长度修饰符

```c
short s = 10;
long l = 1000000;
long long ll = 10000000000LL;
printf("%hd %ld %lld\n", s, l, ll);
```

| 修饰符 | 搭配 | 类型 |
|:---|:---|:---|
| `hh` | `d` `u` `o` `x` | signed/unsigned char |
| `h` | `d` `u` `o` `x` | signed/unsigned short |
| `l` | `d` `u` `o` `x` | signed/unsigned long |
| `ll` | `d` `u` `o` `x` | signed/unsigned long long |
| `L` | `f` `e` `g` | long double |
| `z` | `d` `u` | size_t |

## scanf 家族

### 基本用法

```c
int age;
float height;
scanf("%d %f", &age, &height);   // 必须传地址！
```

**常见错误**：忘记 `&`，传入变量值而非地址：

```c
scanf("%d", age);    // 灾难！把 age 的值当作地址写入
```

### 格式控制

```c
int a, b;
scanf("%d,%d", &a, &b);   // 输入必须包含逗号："10,20"
scanf("%4d", &a);          // 最多读取4位数字
scanf("%*d %d", &a);       // 跳过第一个整数，读取第二个
```

### 读取字符串

```c
char name[100];
scanf("%s", name);          // 读到空白符停止，不检查越界！
scanf("%99s", name);        // 最多读99个字符，留1个给 '\0'
```

**`scanf` 读取字符串的危险**：`%s` 不检查缓冲区大小，是缓冲区溢出漏洞的主要来源。生产环境应使用 `fgets`：

```c
char line[256];
if (fgets(line, sizeof(line), stdin) != NULL) {
    // 去掉末尾的换行符
    line[strcspn(line, "\n")] = '\0';
}
```

### scanf 的返回值

```c
int a, b;
int n = scanf("%d %d", &a, &b);
if (n != 2) {
    printf("输入格式错误，成功读取 %d 个值\n", n);
}
```

`scanf` 返回成功读取的项目数，可用于输入验证。

## 字符I/O

### 单字符读写

```c
int c;   // 注意用 int，不是 char！
while ((c = getchar()) != EOF) {
    putchar(c);
}
```

**为什么用 `int` 接收 `getchar()`？**

`getchar()` 返回 `int`，因为：
1. 需要能返回 `EOF`（通常是 -1）
2. `char` 可能是有符号的，字符 0xFF 会被解释为 -1，与 EOF 混淆

### 行读取

```c
char line[256];
while (fgets(line, sizeof(line), stdin) != NULL) {
    printf("读取到: %s", line);
}
```

`fgets` 会保留换行符，如果行太长会分多次读取。

## 文件操作基础

```c
FILE *fp = fopen("data.txt", "r");
if (fp == NULL) {
    perror("无法打开文件");   // 输出：无法打开文件: No such file or directory
    return 1;
}

char line[256];
while (fgets(line, sizeof(line), fp) != NULL) {
    printf("%s", line);
}

fclose(fp);   // 必须关闭！否则数据可能丢失，资源泄漏
```

### 文件打开模式

| 模式 | 含义 |
|:---|:---|
| `"r"` | 只读，文件必须存在 |
| `"w"` | 只写，文件存在则清空，不存在则创建 |
| `"a"` | 追加写，文件不存在则创建 |
| `"r+"` | 读写，文件必须存在 |
| `"w+"` | 读写，文件存在则清空 |
| `"a+"` | 读写追加，文件不存在则创建 |
| `"rb"` | 二进制只读 |

## 缓冲区机制

### 三种缓冲模式

| 模式 | 触发刷新条件 | 典型应用 |
|:---|:---|:---|
| 全缓冲 | 缓冲区满或 `fflush` | 文件输出 |
| 行缓冲 | 遇到 `\n` 或缓冲区满 | 终端 stdout |
| 无缓冲 | 立即输出 | stderr |

```c
printf("Loading");
for (int i = 0; i < 5; i++) {
    printf(".");
    fflush(stdout);   // 强制刷新，否则可能看不到动态效果
    sleep(1);
}
```

## 常见错误与陷阱

### 1. printf 格式与参数不匹配

```c
int x = 65;
printf("%c", x);    // 输出 A（正确）
printf("%f", x);    // 未定义行为！int 和 double 在内存中布局完全不同
```

### 2. scanf 读取字符时跳过空白

```c
char c;
scanf(" %c", &c);   // %c 前的空格会跳过所有空白符（空格、\t、\n）
```

### 3. 混用 scanf 和 fgets

```c
int age;
scanf("%d", &age);       // 输入 "25\n"，\n 留在缓冲区
char name[100];
fgets(name, sizeof(name), stdin);   // 立即读到空行！
```

**解决**：在 `scanf` 后清空缓冲区：

```c
int c;
while ((c = getchar()) != '\n' && c != EOF);   // 清空到行尾
```

## 学习要点总结

1. `printf` 参数类型必须与格式说明符匹配，否则是未定义行为
2. `scanf` 必须传变量的地址（`&`），字符串名本身就是地址除外
3. 读取字符串优先使用 `fgets` 而非 `scanf("%s")`，防止缓冲区溢出
4. `getchar()` 返回 `int`，不是 `char`
5. 理解缓冲区机制，需要即时输出时使用 `fflush`
