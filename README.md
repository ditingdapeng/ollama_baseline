# 甄嬛传角色对话系统 (Ollama Baseline)

基于《甄嬛传》角色数据的智能对话系统，使用 LoRA 微调技术训练甄嬛角色模型，支持多种交互方式。

## 📁 项目结构

```
ollama_baseline/
├── application/          # Web应用界面
│   └── huanhuan_web.py  # Streamlit对话界面
├── dataScripts/         # 数据处理脚本
│   ├── huanhuan_data_prepare.py  # 训练数据预处理
│   └── download_data.py          # 数据集下载
├── deployment/          # 模型部署
│   ├── FAST_DEPLOYMENT_GUIDE.md  # 快速部署指南
│   ├── Modelfile.huanhuan        # Ollama模型文件
│   └── huanhuan_fast_lora.gguf   # LoRA权重文件
├── mcp_server/          # MCP服务器
│   ├── __init__.py      # 服务器入口
│   └── server.py        # MCP服务器核心逻辑
├── training/            # 模型训练
│   ├── huanhuan_train.py        # 训练脚本
│   ├── huanhuan_config.yaml     # 训练配置
│   ├── huanhuan_config_fast.yaml # 快速训练配置
│   └── logs/                    # 训练日志
├── data/               # 数据目录
├── requirements.txt    # 项目依赖
└── README.md          # 项目说明
```

## 🚀 功能模块

### 📱 Web应用 (application)
- **huanhuan_web.py**: 基于 Streamlit 的甄嬛角色对话Web界面
- 支持实时对话、参数调节、聊天历史管理
- 提供直观的用户界面和流式对话体验

### 📊 数据处理 (dataScripts)
- **huanhuan_data_prepare.py**: 甄嬛传训练数据预处理脚本
- **download_data.py**: 从GitHub下载甄嬛传数据集
- 支持数据清洗、格式转换、分割等功能

### 🚀 模型部署 (deployment)
- **FAST_DEPLOYMENT_GUIDE.md**: 详细的快速部署指南
- **Modelfile.huanhuan**: Ollama模型配置文件
- **huanhuan_fast_lora.gguf**: 训练好的LoRA权重文件
- 支持一键部署到Ollama服务

### 🔌 MCP服务器 (mcp_server)
- **server.py**: MCP (Model Context Protocol) 服务器实现
- 提供与甄嬛模型交互的API接口
- 支持对话、模型信息查询、状态检查等功能

### 🎯 模型训练 (training)
- **huanhuan_train.py**: 甄嬛角色模型训练脚本
- **huanhuan_config.yaml**: 完整训练配置
- **huanhuan_config_fast.yaml**: 快速训练配置
- 基于LoRA技术进行高效微调
- 支持GPU/MPS/CPU多种设备

## 📦 安装依赖

### 方式一：使用 pip 安装

```bash
pip install -r requirements.txt
```

### 方式二：使用 conda 环境（推荐）

```bash
# 1. 创建conda环境（指定Python版本）
conda create -n huanhuan python=3.13

# 2. 激活环境
conda activate huanhuan

# 3. 安装依赖
pip install -r requirements.txt
# 或者优先使用conda安装
conda install pytorch transformers -c pytorch -c huggingface
pip install -r requirements.txt

# 4. 退出环境
conda deactivate
```

### 方式三：使用 uv

```bash
# 1. 安装uv（如果未安装）
pip install uv

# 2. 创建虚拟环境
uv venv huanhuan_env

# 3. 激活环境
source huanhuan_env/bin/activate  # macOS/Linux

# 4. 使用uv安装依赖（比pip快10-100倍）
uv pip install -r requirements.txt
```

