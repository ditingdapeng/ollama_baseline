#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
甄嬛角色Web对话界面

基于Streamlit的甄嬛角色对话Web应用
参考: https://github.com/KMnO4-zx/huanhuan-chat

使用方法:
    streamlit run application/huanhuan_web.py
    streamlit run application/huanhuan_web.py --server.port 8501
"""

import os
import sys
import json
import requests
import streamlit as st
from pathlib import Path
from typing import List, Dict
import time
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 页面配置
st.set_page_config(
    page_title="Chat-嬛嬛 - 甄嬛传角色对话",
    page_icon="👸",
    layout="wide",
    initial_sidebar_state="expanded"
)

class HuanHuanWebApp:
    """
    甄嬛Web应用
    """
    
    def __init__(self):
        self.ollama_host = "http://localhost:11434"
        self.model_name = "huanhuan-qwen"
        
        # 初始化session state
        self.init_session_state()
    
    def init_session_state(self):
        """
        初始化会话状态
        """
        # 对话历史
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Ollama连接状态
        if "ollama_connected" not in st.session_state:
            st.session_state.ollama_connected = False
        
        # 可用模型列表
        if "available_models" not in st.session_state:
            st.session_state.available_models = []
        
        # 当前选择的模型
        if "selected_model" not in st.session_state:
            st.session_state.selected_model = None
        
        # 生成参数
        if "temperature" not in st.session_state:
            st.session_state.temperature = 0.7
        if "top_p" not in st.session_state:
            st.session_state.top_p = 0.9
        if "top_k" not in st.session_state:
            st.session_state.top_k = 40
        if "max_tokens" not in st.session_state:
            st.session_state.max_tokens = 256
        
        # 对话历史记录
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
    
    def check_ollama_connection(self) -> bool:
        """
        检查Ollama服务连接状态
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                st.session_state.ollama_connected = True
                return True
        except requests.exceptions.RequestException:
            pass
        
        st.session_state.ollama_connected = False
        return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用的模型列表
        """
        if not self.check_ollama_connection():
            return []
        
        try:
            response = requests.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                st.session_state.available_models = models
                return models
        except Exception as e:
            st.error(f"获取模型列表失败: {e}")
        
        return []
    
    def stream_chat(self, messages, model):
        """
        流式对话生成
        """
        url = f"{self.ollama_host}/api/chat"
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": st.session_state.temperature,
                "top_p": st.session_state.top_p,
                "top_k": st.session_state.top_k
            }
        }
        
        try:
            response = requests.post(url, json=payload, stream=True, timeout=60)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        if 'message' in data and 'content' in data['message']:
                            yield data['message']['content']
                        
                        if data.get('done', False):
                            break
                    except json.JSONDecodeError:
                        continue
                        
        except requests.exceptions.RequestException as e:
            yield f"连接错误: {e}"
        except Exception as e:
            yield f"未知错误: {e}"
    
    def render_sidebar(self):
        """
        渲染侧边栏
        """
        with st.sidebar:
            st.title("⚙️ 设置")
            
            # 连接状态
            if self.check_ollama_connection():
                st.success("🟢 Ollama服务已连接")
            else:
                st.error("🔴 Ollama服务未连接")
                st.info("请确保Ollama服务正在运行")
            
            st.divider()
            
            # 模型选择
            st.subheader("🤖 模型设置")
            available_models = self.get_available_models()
            
            if available_models:
                if self.model_name in available_models:
                    default_index = available_models.index(self.model_name)
                else:
                    default_index = 0
                
                selected_model = st.selectbox(
                    "选择模型",
                    available_models,
                    index=default_index
                )
                st.session_state.selected_model = selected_model
                self.model_name = selected_model
            else:
                st.warning("未找到可用模型")
                st.info("请先部署甄嬛模型")
            
            st.divider()
            
            # 参数调节
            st.subheader("🎛️ 生成参数")
            
            st.session_state.temperature = st.slider(
                "Temperature (创造性)",
                min_value=0.1,
                max_value=2.0,
                value=st.session_state.temperature,
                step=0.1,
                help="控制回答的随机性，值越高越有创造性"
            )
            
            st.session_state.top_p = st.slider(
                "Top P (多样性)",
                min_value=0.1,
                max_value=1.0,
                value=st.session_state.top_p,
                step=0.1,
                help="控制词汇选择的多样性"
            )
            
            st.session_state.top_k = st.slider(
                "Top K (词汇范围)",
                min_value=1,
                max_value=100,
                value=st.session_state.top_k,
                step=1,
                help="限制每步选择的词汇数量"
            )
            
            st.session_state.max_tokens = st.slider(
                "Max Tokens (回答长度)",
                min_value=50,
                max_value=500,
                value=st.session_state.max_tokens,
                step=10,
                help="控制回答的最大长度"
            )
            
            st.divider()
            
            # 功能按钮
            st.subheader("🛠️ 功能")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🗑️ 清空对话", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.chat_history = []
                    st.rerun()
            
            with col2:
                if st.button("💾 保存对话", use_container_width=True):
                    if st.session_state.chat_history:
                        self.save_chat_history()
                        st.success("对话已保存！")
                    else:
                        st.warning("没有对话内容可保存")
            
            with col3:
                if st.button("📂 加载对话", use_container_width=True):
                    self.load_chat_history()
    
    def render_main_content(self):
        """
        渲染主要内容
        """
        # 标题和介绍
        st.title("👸 Chat-嬛嬛")
        st.markdown("""
        欢迎来到甄嬛传角色对话系统！我是甄嬛，大理寺少卿甄远道之女。
        臣妾愿与您畅谈宫廷生活、诗词歌赋，分享人生感悟。
        """)
        
        # 角色信息卡片
        with st.expander("📖 角色信息", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                **基本信息**
                - 姓名：甄嬛（甄玉嬛）
                - 身份：熹贵妃
                - 出身：大理寺少卿甄远道之女
                - 特长：诗词歌赋、琴棋书画
                """)
            
            with col2:
                st.markdown("""
                **性格特点**
                - 聪慧机智，善于应变
                - 温婉贤淑，知书达理
                - 坚韧不拔，重情重义
                - 语言典雅，谦逊有礼
                """)
        
        # 示例问题
        st.subheader("💡 示例问题")
        example_questions = [
            "你好，请介绍一下自己",
            "你觉得宫廷生活如何？",
            "如何看待友情？",
            "能为我作一首诗吗？",
            "给后人一些人生建议",
            "你最喜欢什么？"
        ]
        
        cols = st.columns(3)
        for i, question in enumerate(example_questions):
            with cols[i % 3]:
                if st.button(question, key=f"example_{i}", use_container_width=True):
                    st.session_state.current_question = question
        
        st.divider()
        
        # 对话历史
        st.subheader("💬 对话历史")
        
        # 显示对话消息
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 处理示例问题
        if hasattr(st.session_state, 'current_question'):
            user_input = st.session_state.current_question
            delattr(st.session_state, 'current_question')
        else:
            user_input = None
        
        # 聊天输入
        if prompt := st.chat_input("请输入您的问题...") or user_input:
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 生成回复
            with st.chat_message("assistant"):
                with st.spinner("甄嬛正在思考..."):
                    # 使用流式生成
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    # 构建消息历史
                    messages = []
                    for msg in st.session_state.messages:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })
                    
                    for chunk in self.stream_chat(messages, st.session_state.selected_model):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
            
            # 添加助手消息
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # 保存到历史记录
            st.session_state.chat_history.append({
                "timestamp": datetime.now().isoformat(),
                "user": prompt,
                "assistant": full_response,
                "params": {
                    "temperature": st.session_state.temperature,
                    "top_p": st.session_state.top_p,
                    "top_k": st.session_state.top_k,
                    "max_tokens": st.session_state.max_tokens
                }
            })
    
    def save_chat_history(self):
        """
        保存对话历史
        """
        if not st.session_state.chat_history:
            return
        
        # 创建保存目录
        save_dir = Path("application/chat_history")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"huanhuan_chat_{timestamp}.json"
        filepath = save_dir / filename
        
        # 保存数据
        save_data = {
            "timestamp": timestamp,
            "chat_history": st.session_state.chat_history,
            "model_params": {
                "selected_model": st.session_state.selected_model,
                "temperature": st.session_state.temperature,
                "top_p": st.session_state.top_p,
                "top_k": st.session_state.top_k,
                "max_tokens": st.session_state.max_tokens
            }
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"保存失败: {e}")
    
    def load_chat_history(self):
        """
        加载对话历史
        """
        save_dir = Path("application/chat_history")
        if not save_dir.exists():
            st.warning("没有找到历史对话文件")
            return
        
        # 获取所有历史文件
        history_files = list(save_dir.glob("*.json"))
        if not history_files:
            st.warning("没有找到历史对话文件")
            return
        
        # 选择文件
        file_options = {f.name: f for f in sorted(history_files, reverse=True)}
        selected_file = st.selectbox(
            "选择要加载的对话:",
            options=list(file_options.keys())
        )
        
        if st.button("加载选中的对话"):
            try:
                with open(file_options[selected_file], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                st.session_state.chat_history = data.get('chat_history', [])
                st.session_state.messages = []
                
                # 重建messages格式
                for chat in st.session_state.chat_history:
                    st.session_state.messages.append({"role": "user", "content": chat["user"]})
                    st.session_state.messages.append({"role": "assistant", "content": chat["assistant"]})
                
                # 加载模型参数
                if 'model_params' in data:
                    params = data['model_params']
                    if 'selected_model' in params:
                        st.session_state.selected_model = params['selected_model']
                    if 'temperature' in params:
                        st.session_state.temperature = params['temperature']
                    if 'top_p' in params:
                        st.session_state.top_p = params['top_p']
                    if 'top_k' in params:
                        st.session_state.top_k = params['top_k']
                    if 'max_tokens' in params:
                        st.session_state.max_tokens = params['max_tokens']
                
                st.success(f"已加载对话: {selected_file}")
                st.rerun()
            except Exception as e:
                st.error(f"加载失败: {e}")
    
    def get_history_files(self):
        """
        获取历史文件列表
        """
        save_dir = Path("application/chat_history")
        if not save_dir.exists():
            return []
        
        history_files = list(save_dir.glob("*.json"))
        return sorted([f.name for f in history_files], reverse=True)
    
    def render_footer(self):
        """
        渲染页脚
        """
        st.divider()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📊 统计信息**")
            st.metric("对话轮数", len(st.session_state.messages) // 2)
        
        with col2:
            st.markdown("**🔧 技术栈**")
            st.markdown("Streamlit + Ollama + LoRA")
        
        with col3:
            st.markdown("**📚 参考项目**")
            st.markdown("[huanhuan-chat](https://github.com/KMnO4-zx/huanhuan-chat)")
    
    def run(self):
        """
        运行应用主方法
        """
        # 渲染侧边栏
        self.render_sidebar()
        
        # 渲染主要内容
        self.render_main_content()
        
        # 渲染页脚
        self.render_footer()

def main():
    """
    主函数
    """
    # 自定义CSS
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    
    .stButton > button {
        border-radius: 20px;
        border: none;
        background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 创建并运行应用
    app = HuanHuanWebApp()
    app.run()

if __name__ == "__main__":
    main()