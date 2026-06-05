# C语言位运算与底层操作

## 位运算基础

C语言提供6种位运算符，直接操作整数的二进制位：

| 运算符 | 名称 | 示例 | 结果 |
|:---|:---|:---|:---|
| `&` | 按位与 | `0b1100 & 0b1010` | `0b1000` |
| `\|` | 按位或 | `0b1100 \| 0b1010` | `0b1110` |
| `^` | 按位异或 | `0b1100 ^ 0b1010` | `0b0110` |
| `~` | 按位取反 | `~0b1100` | `0b0011`（假设4位） |
| `<<` | 左移 | `0b0001 << 2` | `0b0100` |
| `>>` | 右移 | `0b0100 >> 1` | `0b0010` |

## 位运算的应用

### 1. 标志位（Flags）

```c
#define FLAG_READ   0x01   // 0001
#define FLAG_WRITE  0x02   // 0010
#define FLAG_EXEC   0x04   // 0100
#define FLAG_DELETE 0x08   // 1000

unsigned int permissions = FLAG_READ | FLAG_WRITE;   // 设置读和写权限

// 检查权限
if (permissions & FLAG_READ) {
    printf("有读权限\n");
}

// 添加权限
permissions |= FLAG_EXEC;   // 添加执行权限

// 移除权限
permissions &= ~FLAG_WRITE;  // 移除写权限

// 切换权限
permissions ^= FLAG_DELETE;  // 切换删除权限
```

### 2. 掩码操作

```c
// 提取低4位
unsigned int value = 0xABCD;
unsigned int low = value & 0x0F;   // 0x0D

// 提取高4位
unsigned int high = (value >> 12) & 0x0F;   // 0x0A

// 设置第 n 位
value |= (1 << n);

// 清除第 n 位
value &= ~(1 << n);

// 切换第 n 位
value ^= (1 << n);

// 检查第 n 位
if (value & (1 << n)) {
    printf("第 %d 位为1\n", n);
}
```

### 3. 位域的替代方案

```c
// 用位运算替代位域（更可控）
#define POS_X_MASK   0x0000FFFF
#define POS_Y_MASK   0xFFFF0000
#define POS_Y_SHIFT  16

uint32_t pack_position(uint16_t x, uint16_t y) {
    return (x & POS_X_MASK) | ((uint32_t)y << POS_Y_SHIFT);
}

void unpack_position(uint32_t packed, uint16_t *x, uint16_t *y) {
    *x = packed & POS_X_MASK;
    *y = (packed & POS_Y_MASK) >> POS_Y_SHIFT;
}
```

## 移位运算的陷阱

### 左移

```c
unsigned int a = 1;
a << 33;   // 未定义行为！移位位数 >= 类型宽度（假设 int 32位）

unsigned int b = 0x80000000;
b << 1;    // 未定义行为！左移导致符号位变化（有符号数）
```

**规则**：
- 移位位数必须小于类型宽度
- 左移时，移出的位丢弃，右侧补0
- 有符号数左移导致符号位变化是未定义行为

### 右移

```c
// 逻辑右移（无符号数）
unsigned int u = 0xFFFFFFFF;
u >> 1;    // 0x7FFFFFFF，最高位补0

// 算术右移（有符号数）
int s = -1;     // 0xFFFFFFFF（补码）
s >> 1;         // 0xFFFFFFFF（最高位补1，保持符号）

int t = -8;     // 0xFFFFFFF8
t >> 1;         // 0xFFFFFFFC（-4），等价于除以2
```

**注意**：C标准不保证有符号数的右移是算术右移，但几乎所有编译器都这么做。

## 大小端（Endianness）

### 检测大小端

```c
union EndianCheck {
    uint32_t i;
    uint8_t c[4];
};

int is_little_endian(void) {
    union EndianCheck e;
    e.i = 0x01020304;
    return e.c[0] == 0x04;   // 小端：低字节在低地址
}
```

### 字节序转换

```c
uint16_t swap16(uint16_t x) {
    return (x << 8) | (x >> 8);
}

uint32_t swap32(uint32_t x) {
    return ((x << 24) & 0xFF000000) |
           ((x << 8)  & 0x00FF0000) |
           ((x >> 8)  & 0x0000FF00) |
           ((x >> 24) & 0x000000FF);
}

// 标准库函数（POSIX）
#include <arpa/inet.h>
uint32_t htonl(uint32_t hostlong);   // 主机字节序转网络字节序（大端）
uint16_t htons(uint16_t hostshort);
uint32_t ntohl(uint32_t netlong);    // 网络字节序转主机字节序
uint16_t ntohs(uint16_t netshort);
```

## 位运算技巧

### 判断奇偶

```c
if (n & 1) {
    printf("奇数\n");
} else {
    printf("偶数\n");
}
```

### 交换两个数（不使用临时变量）

```c
a ^= b;
b ^= a;
a ^= b;
```

**注意**：如果 `a` 和 `b` 指向同一变量，结果会变成0。实际工程中还是用临时变量。

### 计算二进制中1的个数

```c
int count_bits(uint32_t n) {
    int count = 0;
    while (n) {
        n &= (n - 1);   // 清除最低位的1
        count++;
    }
    return count;
}

// 或使用内置函数
int count = __builtin_popcount(n);   // GCC/Clang
```

### 获取最低位的1

```c
int lowest_bit = n & (-n);   // 提取最低位的1
```

### 判断是否为2的幂

```c
int is_power_of_two(uint32_t n) {
    return n && !(n & (n - 1));
}
```

## 位运算与性能

### 用位运算替代乘除法

```c
// 乘以2的幂
x << 3;   // 等价于 x * 8，但现代编译器会自动优化

// 除以2的幂（无符号数）
x >> 2;   // 等价于 x / 4

// 取模2的幂
x & 0x0F;   // 等价于 x % 16（仅当除数是2的幂时）
```

**注意**：现代编译器会自动将乘除法优化为移位，手写移位不一定更快，而且可读性更差。

## 常见错误

### 1. 混淆逻辑运算和位运算

```c
if (flags & MASK) { }     // 位与，检查标志位
if (flags && MASK) { }    // 逻辑与，两个都非0则为真
```

### 2. 有符号数的位运算

```c
int x = -1;
unsigned int y = x >> 1;   // 先算术右移，然后转为无符号，结果很大

// 正确做法
unsigned int y = (unsigned int)x >> 1;   // 先转无符号，再逻辑右移
```

### 3. 移位溢出

```c
unsigned int x = 1;
x << 32;   // 未定义行为！int 通常是32位
```

### 4. 优先级错误

```c
if (x & MASK == 0) { }   // 等价于 x & (MASK == 0)，不是 (x & MASK) == 0
```

## 学习要点总结

1. 位运算直接操作二进制位，用于标志位、掩码、底层数据打包
2. 移位位数必须小于类型宽度，有符号数左移导致符号位变化是未定义行为
3. 大小端影响多字节数据的存储顺序，网络传输需要统一为大端
4. 位运算优先级低于比较运算符，复杂表达式用括号
5. 现代编译器会自动优化乘除法为移位，优先保证代码可读性
