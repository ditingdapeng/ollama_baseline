import os
import sys
import json
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from mcp.server.fastmcp import FastMCP

def get_ollama_host() -> str:
    """Get the Ollama host from environment variables"""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434")

def get_model_name() -> str:
    """Get the model name from environment variables"""
    return os.getenv("HUANHUAN_MODEL", "huanhuan_fast")

OLLAMA_HOST = get_ollama_host()
MODEL_NAME = get_model_name()

mcp = FastMCP("huanhuan-chat")

@mcp.tool()
def chat_with_huanhuan(message: str, temperature: Optional[float] = 0.7, top_p: Optional[float] = 0.9, top_k: Optional[int] = 40, max_tokens: Optional[int] = 256) -> Dict[str, Any]:
    """与甄嬛进行对话交流
    
    Args:
        message (str): 用户发送给甄嬛的消息
        temperature (Optional[float]): 控制回复的随机性，范围0.1-2.0，默认0.7
        top_p (Optional[float]): 核采样参数，范围0.1-1.0，默认0.9
        top_k (Optional[int]): Top-k采样参数，范围1-100，默认40
        max_tokens (Optional[int]): 最大生成token数，范围50-500，默认256
        
    Returns:
        Dict[str, Any]: 包含甄嬛回复和相关信息的字典
    """
    try:
        # 构建请求数据
        request_data = {
            "model": MODEL_NAME,
            "prompt": message,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "num_predict": max_tokens
            }
        }
        
        # 发送请求到Ollama
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "response": result.get('response', '抱歉，臣妾暂时无法回应。'),
            "model": MODEL_NAME,
            "timestamp": datetime.now().isoformat(),
            "params": {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_tokens": max_tokens
            },
            "total_duration": result.get('total_duration'),
            "load_duration": result.get('load_duration'),
            "prompt_eval_count": result.get('prompt_eval_count'),
            "eval_count": result.get('eval_count')
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Ollama请求失败: {str(e)}"}
    except Exception as e:
        return {"error": f"对话处理失败: {str(e)}"}

@mcp.tool()
def get_model_info() -> Dict[str, Any]:
    """获取当前嬛嬛模型的信息
    
    Returns:
        Dict[str, Any]: 模型信息，包括名称、大小、修改时间等
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('models', [])
        
        # 查找嬛嬛模型
        huanhuan_model = None
        for model in models:
            if MODEL_NAME in model.get('name', ''):
                huanhuan_model = model
                break
        
        if huanhuan_model:
            return {
                "name": huanhuan_model.get('name'),
                "size": huanhuan_model.get('size'),
                "digest": huanhuan_model.get('digest'),
                "modified_at": huanhuan_model.get('modified_at'),
                "details": huanhuan_model.get('details', {})
            }
        else:
            return {"error": f"未找到模型 {MODEL_NAME}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"获取模型信息失败: {str(e)}"}
    except Exception as e:
        return {"error": f"处理失败: {str(e)}"}

@mcp.tool()
def list_available_models() -> Dict[str, Any]:
    """列出Ollama中所有可用的模型
    
    Returns:
        Dict[str, Any]: 包含所有可用模型列表的字典
    """
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('models', [])
        
        model_list = []
        for model in models:
            model_list.append({
                "name": model.get('name'),
                "size": model.get('size'),
                "modified_at": model.get('modified_at')
            })
        
        return {
            "models": model_list,
            "total_count": len(model_list),
            "current_model": MODEL_NAME
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"获取模型列表失败: {str(e)}"}
    except Exception as e:
        return {"error": f"处理失败: {str(e)}"}

@mcp.tool()
def check_ollama_status() -> Dict[str, Any]:
    """检查Ollama服务的运行状态
    
    Returns:
        Dict[str, Any]: Ollama服务状态信息
    """
    try:
        # 检查Ollama是否运行
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            # 检查嬛嬛模型是否存在
            huanhuan_available = any(MODEL_NAME in model.get('name', '') for model in models)
            
            return {
                "status": "running",
                "host": OLLAMA_HOST,
                "model_name": MODEL_NAME,
                "model_available": huanhuan_available,
                "total_models": len(models),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "error": f"Ollama响应状态码: {response.status_code}",
                "host": OLLAMA_HOST
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "status": "disconnected",
            "error": "无法连接到Ollama服务",
            "host": OLLAMA_HOST,
            "suggestion": "请确保Ollama服务正在运行"
        }
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "error": "连接Ollama服务超时",
            "host": OLLAMA_HOST
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"检查状态失败: {str(e)}",
            "host": OLLAMA_HOST
        }

@mcp.tool()
def roleplay_conversation(scenario: str, user_message: str, character_mood: Optional[str] = "平和", temperature: Optional[float] = 0.8) -> Dict[str, Any]:
    """进行角色扮演对话，设定特定场景和甄嬛的情绪状态
    
    Args:
        scenario (str): 对话场景描述，如"在御花园中", "在甘露殿内", "在冷宫中"等
        user_message (str): 用户在该场景下对甄嬛说的话
        character_mood (Optional[str]): 甄嬛的情绪状态，如"愉悦", "忧郁", "愤怒", "平和"等，默认"平和"
        temperature (Optional[float]): 控制回复的创造性，范围0.1-2.0，默认0.8
        
    Returns:
        Dict[str, Any]: 包含甄嬛在特定场景和情绪下的回复
    """
    try:
        # 构建角色扮演的提示词
        roleplay_prompt = f"""场景设定：{scenario}
甄嬛当前的情绪状态：{character_mood}

请以甄嬛的身份，在上述场景和情绪状态下，回应以下话语：
{user_message}

请保持甄嬛的说话风格和性格特点，回复要符合场景氛围和当前情绪。"""
        
        request_data = {
            "model": MODEL_NAME,
            "prompt": roleplay_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 300
            }
        }
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "response": result.get('response', '臣妾一时语塞，不知如何回应。'),
            "scenario": scenario,
            "character_mood": character_mood,
            "user_message": user_message,
            "model": MODEL_NAME,
            "timestamp": datetime.now().isoformat(),
            "params": {
                "temperature": temperature
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"角色扮演对话失败: {str(e)}"}
    except Exception as e:
        return {"error": f"处理失败: {str(e)}"}

@mcp.tool()
def poetry_interaction(poetry_type: str, user_input: str, temperature: Optional[float] = 0.9) -> Dict[str, Any]:
    """与甄嬛进行诗词相关的互动交流
    
    Args:
        poetry_type (str): 诗词类型，如"作诗", "对对联", "诗词赏析", "填词"等
        user_input (str): 用户的诗词相关输入，如诗句、上联、要赏析的诗词等
        temperature (Optional[float]): 控制创作的创造性，范围0.1-2.0，默认0.9
        
    Returns:
        Dict[str, Any]: 甄嬛的诗词回应和创作
    """
    try:
        # 根据诗词类型构建不同的提示词
        if poetry_type == "作诗":
            prompt = f"请以甄嬛的身份，根据以下主题或要求作一首诗：\n{user_input}\n\n请体现甄嬛的文学素养和情感特色。"
        elif poetry_type == "对对联":
            prompt = f"请以甄嬛的身份，为以下上联对出下联：\n上联：{user_input}\n\n请对出工整、有意境的下联。"
        elif poetry_type == "诗词赏析":
            prompt = f"请以甄嬛的身份，赏析以下诗词：\n{user_input}\n\n请从意境、情感、技法等方面进行品评。"
        elif poetry_type == "填词":
            prompt = f"请以甄嬛的身份，按照以下词牌或要求填词：\n{user_input}\n\n请创作出符合词牌格律和甄嬛性格的词作。"
        else:
            prompt = f"请以甄嬛的身份，就以下诗词相关内容进行回应：\n类型：{poetry_type}\n内容：{user_input}"
        
        request_data = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 50,
                "num_predict": 400
            }
        }
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        
        return {
            "response": result.get('response', '臣妾才疏学浅，一时难以应对。'),
            "poetry_type": poetry_type,
            "user_input": user_input,
            "model": MODEL_NAME,
            "timestamp": datetime.now().isoformat(),
            "params": {
                "temperature": temperature
            }
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"诗词互动失败: {str(e)}"}
    except Exception as e:
        return {"error": f"处理失败: {str(e)}"}