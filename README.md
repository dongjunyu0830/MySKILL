# home_work

一个基础的 Python 项目环境，已配置好虚拟环境和常用依赖包。

## 环境要求

- Python 3.9+

## 快速开始

### 1. 激活虚拟环境

```bash
source venv/bin/activate
```

激活后命令行前面会出现 `(venv)` 标识。

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 退出虚拟环境

```bash
deactivate
```

## 日常使用

### 新增依赖

安装新的包后，把它更新到 `requirements.txt`：

```bash
pip install <包名>
pip freeze > requirements.txt
```

### 运行 Python 脚本

```bash
python your_script.py
```

### 运行测试

```bash
pytest
```

### 代码格式化与检查

```bash
# 自动格式化代码
black .

# 静态检查
flake8 .
```

## 已安装的常用包

| 类别 | 包 | 说明 |
|------|------|------|
| HTTP 请求 | requests | 发送 HTTP 请求 |
| 科学计算 | numpy | 数值计算 |
| 数据处理 | pandas | 数据分析与处理 |
| 可视化 | matplotlib | 绘图 |
| 测试 | pytest | 单元测试框架 |
| 代码格式化 | black | 自动格式化 |
| 静态检查 | flake8 | 代码风格检查 |
| 环境变量 | python-dotenv | 从 .env 加载环境变量 |

## 目录结构

```
home_work/
├── .gitignore          # Git 忽略配置
├── README.md           # 项目说明
├── requirements.txt    # 依赖清单
└── venv/               # 虚拟环境（已被 .gitignore 忽略）
```

## 说明

- `venv/` 目录已加入 `.gitignore`，不会提交到 Git。
- 如果在受限网络（如公司内网）安装失败，可指定内部镜像源：

```bash
pip install -r requirements.txt -i <公司镜像地址>
```
