"""
FastAPI 后端 - 阶段1：基础架构
目标：实现基本的聊天功能，为后续RAG做准备
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# 加载环境变量
load_dotenv()

# 初始化 FastAPI
app = FastAPI(
    title="医学知识问答系统",
    description="基于 RAG 的垂直领域问答机器人",
    version="0.1.0"
)

# 配置 CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置代理（如果需要）
if os.getenv("HTTPS_PROXY"):
    proxy = os.getenv("HTTPS_PROXY")
    print(f"🌐 使用代理: {proxy}")
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy

# 初始化 Google AI
api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    raise ValueError("❌ 请在 .env 文件中设置 GOOGLE_AI_API_KEY")

genai.configure(api_key=api_key)

# ==========================================
# 数据模型
# ==========================================
class Message(BaseModel):
    """单条消息"""
    role: str  # "user" 或 "assistant"
    content: str

class ChatRequest(BaseModel):
    """聊天请求"""
    messages: List[Message]

# ==========================================
# 核心功能
# ==========================================

async def generate_stream(messages: List[Message]):
    """
    生成流式响应（阶段1：直接调用Gemini）
    """
    try:
        # 获取 Gemini 模型
        model = genai.GenerativeModel('gemini-2.5-flash')

    # 平衡速度和质量（推荐）
    # genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    # 快速但质量略低
    #  genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
    # 最高质量但较慢
    # genAI.getGenerativeModel({ model: 'gemini-2.5-pro' });
        
        # 构建对话历史
        chat_history = []
        for msg in messages[:-1]:  # 除了最后一条
            chat_history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [msg.content]
            })
        
        # 创建对话
        chat = model.start_chat(history=chat_history)
        
        # 获取最后一条用户消息
        user_message = messages[-1].content
        
        print(f"📨 收到用户消息: {user_message[:50]}...")
        
        # 流式生成
        response = chat.send_message(user_message, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
        print("✅ 响应生成完成")
        
    except Exception as e:
        error_msg = f"生成响应时出错: {str(e)}"
        print(f"❌ {error_msg}")
        yield f"\n\n[错误: {error_msg}]"

# ==========================================
# API 路由
# ==========================================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "message": "医学知识问答系统 API",
        "version": "0.1.0",
        "stage": "阶段1：基础架构"
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    聊天接口（流式响应）
    阶段1：直接调用 Gemini，不使用 RAG
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        # 返回流式响应
        return StreamingResponse(
            generate_stream(request.messages),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        print(f"❌ 聊天接口错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查（详细信息）"""
    return {
        "status": "healthy",
        "google_ai_configured": bool(os.getenv("GOOGLE_AI_API_KEY")),
        "proxy_enabled": bool(os.getenv("HTTPS_PROXY")),
    }

# ==========================================
# 启动服务
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    print(f"""
    ==========================================
    🚀 启动医学知识问答系统后端
    ==========================================
    📍 地址: http://{host}:{port}
    📖 文档: http://{host}:{port}/docs
    🔧 阶段: 阶段1 - 基础架构
    ==========================================
    """)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式自动重载
        log_level="info"
    )