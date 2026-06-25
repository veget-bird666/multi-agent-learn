# Python 模块与包

## 模块 (Module)

一个 `.py` 文件就是一个模块：

```python
# math_utils.py
PI = 3.14159

def circle_area(r: float) -> float:
    return PI * r ** 2
```

```python
# main.py
import math_utils
from math_utils import circle_area, PI

print(math_utils.circle_area(5))
print(circle_area(5))
```

## import 的几种形式

```python
import os                          # 导入模块
import numpy as np                 # 别名
from pathlib import Path           # 导入特定名称
from collections import *          # 不推荐，污染命名空间
from .utils import helper          # 相对导入（包内）
```

## 包的目录结构

```
myproject/
├── main.py
├── requirements.txt
└── mypackage/
    ├── __init__.py      # 包标识，可为空
    ├── core.py
    └── utils/
        ├── __init__.py
        └── helpers.py
```

```python
from mypackage.core import Processor
from mypackage.utils.helpers import format_date
```

`__init__.py` 使目录被识别为包（Python 3.3+ 命名空间包可省略，但显式更好）。

## pip 与依赖管理

```bash
pip install requests pandas
pip freeze > requirements.txt
pip install -r requirements.txt
```

| 文件 | 用途 |
|:---|:---|
| `requirements.txt` | 列出依赖及版本 |
| `pyproject.toml` | 现代项目配置（PEP 621） |
| `.venv/` | 虚拟环境目录 |

## 标准库精选

| 模块 | 用途 |
|:---|:---|
| `os` / `pathlib` | 文件路径与系统操作 |
| `sys` | 解释器参数、退出 |
| `json` | JSON 序列化 |
| `datetime` | 日期时间 |
| `re` | 正则表达式 |
| `random` | 随机数 |
| `itertools` | 迭代工具 |
| `functools` | 高阶函数 |
| `typing` | 类型注解 |

```python
from pathlib import Path
from datetime import datetime

p = Path("data") / "file.txt"
p.exists()
p.read_text(encoding="utf-8")

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

## `if __name__ == "__main__"`

```python
# utils.py
def helper():
    pass

if __name__ == "__main__":
    # 直接运行 utils.py 时执行
    helper()
```

被 import 时 `__name__` 是模块名；直接运行时 `__name__` 是 `"__main__"`。

## 学习要点总结

1. 模块是 `.py` 文件，包是含 `__init__.py` 的目录
2. 用虚拟环境 + requirements.txt 管理依赖
3. `pathlib` 比字符串拼接路径更现代
4. 避免 `from module import *`
5. 可执行脚本和可导入模块用 `if __name__ == "__main__"` 区分
