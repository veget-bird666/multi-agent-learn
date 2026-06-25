# Python 环境搭建与第一个程序

## Python 是什么？

Python 是**解释型、动态类型**的高级编程语言，以简洁可读著称。代码由解释器逐行执行，无需编译链接。

### 解释型 vs 编译型

```
C 语言:  源码 → 编译器 → 机器码 → 直接运行
Python:  源码 → 解释器 → 字节码 → Python 虚拟机执行
```

Python 先将 `.py` 编译为**字节码** (`.pyc`)，再由 PVM 执行。你通常感知不到这一层，直接 `python script.py` 即可。

## 环境搭建

### 安装 Python

推荐 Python 3.10+。从 [python.org](https://www.python.org) 下载，安装时勾选 **Add Python to PATH**。

```bash
python --version    # Windows 可能是 py --version
pip --version
```

### 虚拟环境（强烈推荐）

隔离项目依赖，避免版本冲突：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活（Linux/macOS）
source .venv/bin/activate

# 安装包
pip install requests
```

## 两种运行方式

### 交互式 REPL

```bash
python
>>> 1 + 2
3
>>> print("Hello")
Hello
>>> exit()
```

适合快速试验代码片段。

### 脚本模式

```python
# hello.py
def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
```

```bash
python hello.py
```

`if __name__ == "__main__"` 表示：**仅在被直接运行时**执行，被 import 时不执行。

## 第一个程序深度解析

```python
name = "Python"
print(f"Hello, {name}!")
```

| 要素 | 说明 |
|:---|:---|
| 无需分号 | 换行即语句结束 |
| 缩进无关语法 | 但 PEP 8 建议 4 空格 |
| `f"..."` | f-string，Python 3.6+ 推荐的字符串格式化 |
| 动态类型 | `name` 无需声明类型 |

## 开发工具

| 工具 | 用途 |
|:---|:---|
| VS Code / Cursor | 编辑器 + Python 扩展 |
| PyCharm | 专业 IDE |
| ipython | 增强版 REPL |
| black / ruff | 代码格式化与检查 |

### 推荐的脚本模板

```python
#!/usr/bin/env python3
"""模块文档字符串：简要说明本文件用途。"""


def main() -> None:
    """程序入口。"""
    pass


if __name__ == "__main__":
    main()
```

## 常见错误

### 1. 缩进错误 (IndentationError)

Python 用缩进表示代码块，混用 Tab 和空格会报错。统一用 **4 个空格**。

### 2. 版本混用

系统可能同时有 Python 2 和 3。本项目使用 **Python 3**，打印是函数 `print()` 而非语句。

### 3. 未激活虚拟环境

全局 `pip install` 可能装错位置。先激活 venv 再安装。

## 学习要点总结

1. Python 是解释型语言，通过 `python script.py` 运行
2. 虚拟环境隔离项目依赖，是工程实践的基础
3. REPL 适合实验，脚本适合完整程序
4. `if __name__ == "__main__"` 是 Python 模块的标准入口写法
5. 遵循 PEP 8：4 空格缩进，snake_case 命名
