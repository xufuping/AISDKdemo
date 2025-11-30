"""
FastAPI 后端 - 阶段2：集成 RAG
目标：从知识库检索相关信息，生成基于知识库的回答
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

# 加载环境变量
load_dotenv()

# 初始化 FastAPI
app = FastAPI(
    title="医学知识问答系统",
    description="基于 RAG 的垂直领域问答机器人",
    version="0.2.0"
)

# 配置 CORS（允许前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Google AI
api_key = os.getenv("GOOGLE_AI_API_KEY")
if not api_key:
    raise ValueError("❌ 请在 .env 文件中设置 GOOGLE_AI_API_KEY")

genai.configure(api_key=api_key)

# ==========================================
# 初始化向量数据库和检索器
# ==========================================
VECTOR_STORE_DIR = "./vector_store"

print("=" * 60)
print("🚀 初始化医学知识问答系统")
print("=" * 60)

# 初始化 Embeddings（使用本地模型）
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    print("✅ 本地 Embedding 模型加载成功")
except Exception as e:
    print(f"❌ Embedding 模型加载失败: {e}")
    embeddings = None

# 初始化向量数据库
vectorstore = None
retriever = None

if os.path.exists(VECTOR_STORE_DIR) and embeddings:
    try:
        vectorstore = Chroma(
            persist_directory=VECTOR_STORE_DIR,
            embedding_function=embeddings,
            collection_name="medical_knowledge"
        )
        
        # 创建检索器（每次检索返回前3个最相关的文档块）
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        
        print(f"✅ 向量数据库加载成功")
        print(f"📁 知识库位置: {VECTOR_STORE_DIR}")
        
        # 测试检索
        test_results = retriever.invoke("高血压")
        print(f"🧪 知识库测试成功，共有 {len(test_results)} 个文档块")
        
    except Exception as e:
        print(f"⚠️ 向量数据库加载失败: {e}")
        print("💡 系统将使用通用问答模式（不使用知识库）")
        retriever = None
else:
    if not os.path.exists(VECTOR_STORE_DIR):
        print(f"⚠️ 未找到向量数据库目录: {VECTOR_STORE_DIR}")
        print("💡 请先运行: python load_documents.py")
    print("💡 系统将使用通用问答模式（不使用知识库）")

print("=" * 60)

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
# 核心功能：RAG 检索和生成
# ==========================================

def retrieve_knowledge(query: str) -> tuple[str, List[str]]:
    """
    从知识库检索相关信息
    
    返回:
        context: 检索到的上下文内容
        sources: 来源文件列表
    """
    if not retriever:
        return "", []
    
    try:
        # 检索相关文档
        docs = retriever.invoke(query)
        
        if not docs:
            return "", []
        
        # 提取内容和来源
        context_parts = []
        sources = []
        
        for i, doc in enumerate(docs, 1):
            # 获取文件名
            source = os.path.basename(doc.metadata.get("source", "未知来源"))
            sources.append(source)
            
            # 构建上下文
            context_parts.append(f"[文档{i}：{source}]\n{doc.page_content}")
        
        context = "\n\n".join(context_parts)
        
        print(f"🔍 检索到 {len(docs)} 个相关文档块")
        for source in set(sources):
            print(f"   📄 {source}")
        
        return context, sources
        
    except Exception as e:
        print(f"⚠️ 检索失败: {e}")
        return "", []

def build_rag_prompt(user_query: str, context: str) -> str:
    """
    构建 RAG 提示词
    
    将检索到的知识库内容和用户问题组合成提示词
    """
    if context:
        # 有知识库内容：使用 RAG 模式
        prompt = f"""你是一个专业的医学知识问答助手。请基于以下知识库内容回答用户的问题。

【知识库内容】
{context}

【用户问题】
{user_query}

【回答要求】
1. 优先使用知识库中的信息回答
2. 回答要准确、专业、易懂
3. 如果知识库中有相关信息，请在回答末尾注明信息来源
4. 如果知识库中没有相关信息，可以使用你的通用知识回答，但要说明这不是来自知识库
5. 回答要简洁明了，分点列出关键信息

请回答："""
    else:
        # 没有知识库内容：使用通用模式
        prompt = f"""你是一个专业的医学知识问答助手。请回答用户的问题。

【用户问题】
{user_query}

【回答要求】
1. 回答要准确、专业、易懂
2. 回答要简洁明了，分点列出关键信息
3. 如果涉及医疗建议，提醒用户咨询专业医生

请回答："""
    
    return prompt

async def generate_stream_with_rag(messages: List[Message]):
    """
    生成流式响应（阶段2：集成 RAG）
    """
    try:
        # 获取最新的用户消息
        user_message = messages[-1].content
        
        print(f"\n📨 收到用户消息: {user_message[:50]}...")
        
        # 步骤1：检索知识库
        context, sources = retrieve_knowledge(user_message)
        
        # 步骤2：构建提示词
        rag_prompt = build_rag_prompt(user_message, context)
        
        # 步骤3：获取 Gemini 模型
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 步骤4：构建对话历史（不包括当前问题，因为已经在 rag_prompt 中）
        chat_history = []
        for msg in messages[:-1]:
            chat_history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [msg.content]
            })
        
        # 步骤5：创建对话并生成响应
        chat = model.start_chat(history=chat_history)
        response = chat.send_message(rag_prompt, stream=True)
        
        # 步骤6：流式输出
        for chunk in response:
            if chunk.text:
                yield chunk.text
        
        # 步骤7：如果有来源，在回答末尾添加来源信息
        if sources:
            unique_sources = list(set(sources))
            sources_text = "\n\n---\n📚 **信息来源**：\n"
            for source in unique_sources:
                sources_text += f"- {source}\n"
            yield sources_text
        
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
    has_knowledge_base = retriever is not None
    
    return {
        "status": "ok",
        "message": "医学知识问答系统 API",
        "version": "0.2.0",
        "stage": "阶段2：RAG 集成",
        "knowledge_base_loaded": has_knowledge_base,
        "features": {
            "rag": has_knowledge_base,
            "general_qa": True
        }
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    聊天接口（流式响应 + RAG）
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="消息列表不能为空")
        
        # 返回流式响应
        return StreamingResponse(
            generate_stream_with_rag(request.messages),
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
        "knowledge_base_loaded": retriever is not None,
        "vector_store_path": VECTOR_STORE_DIR,
        "vector_store_exists": os.path.exists(VECTOR_STORE_DIR)
    }

@app.post("/api/search")
async def search_knowledge(query: str):
    """
    测试接口：直接搜索知识库
    """
    if not retriever:
        raise HTTPException(status_code=503, detail="知识库未加载")
    
    try:
        docs = retriever.invoke(query)
        
        results = []
        for doc in docs:
            results.append({
                "source": os.path.basename(doc.metadata.get("source", "未知")),
                "content": doc.page_content[:200] + "...",
                "metadata": doc.metadata
            })
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    📖 API文档: http://{host}:{port}/docs
    🔧 阶段: 阶段2 - RAG 集成
    📚 知识库: {'已加载 ✅' if retriever else '未加载 ⚠️'}
    ==========================================
    """)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )