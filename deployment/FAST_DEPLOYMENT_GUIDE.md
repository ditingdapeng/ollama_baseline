# 甄嬛快速模型部署指南

基于 Qwen2.5-0.5B + LoRA 微调的甄嬛角色模型部署指南

## 📋 前提条件

### 1. 确认训练完成
确保以下文件存在：
```
training/training/models/huanhuan_fast/
├── adapter_config.json
├── adapter_model.safetensors
├── train_results.json
└── README.md
```

### 2. 安装 Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# 验证安装
ollama --version
```

## 🚀 快速部署

### 方法一：自动部署（推荐）
```bash
# 进入项目目录
cd /Users/dapeng/Code/study/ollama

# 运行部署脚本
python deployment/deploy_huanhuan_fast.py
```

### 方法二：手动部署
```bash
# 1. 启动 Ollama 服务
ollama serve

# 2. 拉取基础模型
ollama pull qwen2.5:0.5b

# 3. 创建模型（需要先创建 Modelfile）
ollama create huanhuan-qwen-fast -f deployment/Modelfile.huanhuan_fast

# 4. 测试模型
ollama run huanhuan-qwen-fast
```

## 🔧 部署脚本功能

### 基本用法
```bash
# 完整部署
python deployment/deploy_huanhuan_fast.py

# 指定模型路径
python deployment/deploy_huanhuan_fast.py --model-path training/training/models/huanhuan_fast

# 仅测试已部署的模型
python deployment/deploy_huanhuan_fast.py --test-only

# 显示部署信息
python deployment/deploy_huanhuan_fast.py --info-only

# 删除模型
python deployment/deploy_huanhuan_fast.py --remove-model huanhuan-qwen-fast
```

### 部署流程
1. ✅ 检查 Ollama 安装
2. ✅ 启动 Ollama 服务
3. ✅ 拉取 Qwen2.5-0.5B 基础模型
4. ✅ 创建包含 LoRA 适配器的 Modelfile
5. ✅ 创建 Ollama 模型
6. ✅ 测试模型对话效果

## 💬 使用模型

### 命令行对话
```bash
ollama run huanhuan-qwen-fast
```

### API 调用
```bash
# 单次对话
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "huanhuan-qwen-fast",
    "prompt": "你好，请介绍一下自己",
    "stream": false
  }'

# 流式对话
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "huanhuan-qwen-fast",
    "prompt": "能为我作一首诗吗？",
    "stream": true
  }'
```

### Python API 调用
```python
import requests

def chat_with_huanhuan(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "huanhuan-qwen-fast",
            "prompt": prompt,
            "stream": False
        }
    )
    
    if response.status_code == 200:
        return response.json()["response"]
    else:
        return f"错误: {response.status_code}"

# 使用示例
print(chat_with_huanhuan("你好，甄嬛"))
print(chat_with_huanhuan("你觉得宫廷生活如何？"))
```

## 📊 模型特点

### 技术规格
- **基础模型**: Qwen2.5-0.5B (约 500M 参数)
- **微调方法**: LoRA (Low-Rank Adaptation)
- **LoRA 配置**:
  - rank (r): 2
  - alpha: 4
  - dropout: 0.1
  - target_modules: q_proj
- **训练时间**: ~70 秒
- **可训练参数**: 86,016 (0.02%)

### 角色特点
- 🎭 **角色**: 甄嬛（《甄嬛传》女主角）
- 💬 **语言风格**: 古典雅致，使用"臣妾"自称
- 🏛️ **背景**: 大理寺少卿甄远道之女，后成为熹贵妃
- 📚 **特长**: 诗词歌赋，温婉贤淑

### 性能优势
- ⚡ **快速推理**: 基于 0.5B 小模型，推理速度快
- 💾 **内存友好**: 显存需求低，适合个人设备
- 🎯 **角色一致**: LoRA 微调保持角色特性
- 🔧 **易于部署**: 支持 Ollama 生态系统

## 🛠️ 故障排除

### 常见问题

#### 1. Ollama 服务无法启动
```bash
# 检查端口占用
lsof -i :11434

# 手动启动服务
ollama serve
```

#### 2. 基础模型下载失败
```bash
# 手动拉取模型
ollama pull qwen2.5:0.5b

# 检查网络连接
curl -I https://ollama.ai
```

#### 3. 模型创建失败
```bash
# 检查 Modelfile 语法
cat deployment/Modelfile.huanhuan_fast

# 删除已存在的模型
ollama rm huanhuan-qwen-fast

# 重新创建
ollama create huanhuan-qwen-fast -f deployment/Modelfile.huanhuan_fast
```

#### 4. 模型回答质量问题
- 检查训练数据质量
- 调整模型参数（temperature, top_p 等）
- 重新训练模型

### 日志查看
```bash
# 查看 Ollama 日志
ollama logs

# 查看部署脚本日志
python deployment/deploy_huanhuan_fast.py --info-only
```

## 📁 文件结构

```
deployment/
├── deploy_huanhuan_fast.py      # 快速部署脚本
├── huanhuan_deploy.py           # 通用部署脚本
├── Modelfile.huanhuan_fast      # Ollama Modelfile (自动生成)
└── FAST_DEPLOYMENT_GUIDE.md     # 本指南

training/training/models/huanhuan_fast/
├── adapter_config.json          # LoRA 配置
├── adapter_model.safetensors    # LoRA 权重
├── train_results.json           # 训练结果
└── README.md                    # 模型说明
```

## 🔄 模型管理

### 列出所有模型
```bash
ollama list
```

### 删除模型
```bash
ollama rm huanhuan-qwen-fast
```

### 更新模型
```bash
# 删除旧模型
ollama rm huanhuan-qwen-fast

# 重新部署
python deployment/deploy_huanhuan_fast.py
```

## 📈 下一步

1. **Web 界面**: 开发基于 Streamlit 的对话界面
2. **API 服务**: 创建 FastAPI 服务包装 Ollama
3. **模型优化**: 调整 LoRA 参数提升效果
4. **数据扩充**: 增加训练数据提升对话质量
5. **多轮对话**: 支持上下文记忆的对话

## 📞 支持

如果遇到问题，请检查：
1. Ollama 是否正确安装和运行
2. 模型文件是否完整
3. 网络连接是否正常
4. 系统资源是否充足

---

**部署完成后，你就可以与甄嬛进行对话了！** 🎉