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
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'model_params' not in st.session_state:
            st.session_state.model_params = {
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
                'max_tokens': 256
            }
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
    
    def check_ollama_connection(self) -> bool:
        """
        检查Ollama连接
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> List[str]:
        """
        获取可用模型列表
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except:
            return []
    
    def chat_with_huanhuan(self, message: str, **params) -> str:
        """
        与甄嬛对话
        """
        try:
            # 构建请求数据
            request_data = {
                "model": self.model_name,
                "prompt": message,
                "stream": False,
                "options": {
                    "temperature": params.get('temperature', 0.7),
                    "top_p": params.get('top_p', 0.9),
                    "top_k": params.get('top_k', 40),
                    "num_predict": params.get('max_tokens', 256)
                }
            }
            
            # 发送请求
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '抱歉，臣妾暂时无法回应。')
            else:
                return f"请求失败，状态码: {response.status_code}"
                
        except Exception as e:
            return f"对话出错: {str(e)}"
    
    def stream_chat_with_huanhuan(self, message: str, **params):
        """
        流式对话
        """
        try:
            request_data = {
                "model": self.model_name,
                "prompt": message,
                "stream": True,
                "options": {
                    "temperature": params.get('temperature', 0.7),
                    "top_p": params.get('top_p', 0.9),
                    "top_k": params.get('top_k', 40),
                    "num_predict": params.get('max_tokens', 256)
                }
            }
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json=request_data,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            if 'response' in data:
                                chunk = data['response']
                                full_response += chunk
                                yield chunk
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                yield f"请求失败，状态码: {response.status_code}"
                
        except Exception as e:
            yield f"对话出错: {str(e)}"
    
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
                self.model_name = selected_model
            else:
                st.warning("未找到可用模型")
                st.info("请先部署甄嬛模型")
            
            st.divider()
            
            # 参数调节
            st.subheader("🎛️ 生成参数")
            
            st.session_state.model_params['temperature'] = st.slider(
                "Temperature (创造性)",
                min_value=0.1,
                max_value=2.0,
                value=st.session_state.model_params['temperature'],
                step=0.1,
                help="控制回答的随机性，值越高越有创造性"
            )
            
            st.session_state.model_params['top_p'] = st.slider(
                "Top P (多样性)",
                min_value=0.1,
                max_value=1.0,
                value=st.session_state.model_params['top_p'],
                step=0.1,
                help="控制词汇选择的多样性"
            )
            
            st.session_state.model_params['top_k'] = st.slider(
                "Top K (词汇范围)",
                min_value=1,
                max_value=100,
                value=st.session_state.model_params['top_k'],
                step=1,
                help="限制每步选择的词汇数量"
            )
            
            st.session_state.model_params['max_tokens'] = st.slider(
                "Max Tokens (回答长度)",
                min_value=50,
                max_value=500,
                value=st.session_state.model_params['max_tokens'],
                step=10,
                help="控制回答的最大长度"
            )
            
            st.divider()
            
            # 功能按钮
            st.subheader("🛠️ 功能")
            
            if st.button("🗑️ 清空对话", use_container_width=True):
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.rerun()
            
            if st.button("💾 保存对话", use_container_width=True):
                self.save_chat_history()
            
            if st.button("📁 加载对话", use_container_width=True):
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
                    
                    for chunk in self.stream_chat_with_huanhuan(prompt, **st.session_state.model_params):
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
                "params": st.session_state.model_params.copy()
            })
    
    def save_chat_history(self):
        """
        保存对话历史
        """
        try:
            history_dir = Path(__file__).parent / "chat_history"
            history_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = history_dir / f"huanhuan_chat_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.chat_history, f, ensure_ascii=False, indent=2)
            
            st.success(f"对话历史已保存: {filename}")
            
        except Exception as e:
            st.error(f"保存失败: {e}")
    
    def load_chat_history(self):
        """
        加载对话历史
        """
        try:
            history_dir = Path(__file__).parent / "chat_history"
            if not history_dir.exists():
                st.warning("没有找到历史记录")
                return
            
            history_files = list(history_dir.glob("huanhuan_chat_*.json"))
            if not history_files:
                st.warning("没有找到历史记录文件")
                return
            
            # 选择最新的文件
            latest_file = max(history_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                loaded_history = json.load(f)
            
            st.session_state.chat_history = loaded_history
            
            # 重建消息列表
            st.session_state.messages = []
            for item in loaded_history:
                st.session_state.messages.append({"role": "user", "content": item["user"]})
                st.session_state.messages.append({"role": "assistant", "content": item["assistant"]})
            
            st.success(f"对话历史已加载: {latest_file.name}")
            st.rerun()
            
        except Exception as e:
            st.error(f"加载失败: {e}")
    
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
        运行Web应用
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