"""
文档加载和向量化脚本（使用本地 Embedding 模型）
功能：加载知识库文档，分块，创建向量嵌入，存入ChromaDB
"""

import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("📚 开始加载知识库文档（使用本地 Embedding 模型）")
print("=" * 60)

# 配置
DATA_DIR = "./data"
VECTOR_STORE_DIR = "./vector_store"

print(f"📁 数据目录: {DATA_DIR}")
print(f"💾 向量库目录: {VECTOR_STORE_DIR}")

# ==========================================
# 步骤1：加载文档
# ==========================================
print("\n🔍 步骤1：加载文档...")

# 加载所有txt文件
loader = DirectoryLoader(
    DATA_DIR,
    glob="**/*.txt",  # 递归搜索所有txt文件
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)

try:
    documents = loader.load()
    print(f"✅ 成功加载 {len(documents)} 个文档")
    
    # 显示加载的文档信息
    for i, doc in enumerate(documents, 1):
        file_name = os.path.basename(doc.metadata.get("source", "未知"))
        content_length = len(doc.page_content)
        print(f"   {i}. {file_name} ({content_length} 字符)")
        
except Exception as e:
    print(f"❌ 加载文档失败: {e}")
    exit(1)

if len(documents) == 0:
    print("⚠️ 没有找到任何文档，请检查data目录")
    exit(1)

# ==========================================
# 步骤2：文档分块
# ==========================================
print("\n✂️ 步骤2：文档分块...")

# 创建文本分割器
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # 每块500字符
    chunk_overlap=50,      # 块之间重叠50字符
    length_function=len,
    separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""]
)

# 分块
try:
    splits = text_splitter.split_documents(documents)
    print(f"✅ 文档已分割为 {len(splits)} 个块")
    
    # 显示第一个块的示例
    if len(splits) > 0:
        print(f"\n📝 示例块（第1块）：")
        print(f"来源：{os.path.basename(splits[0].metadata.get('source', ''))}")
        print(f"内容：{splits[0].page_content[:100]}...")
        
except Exception as e:
    print(f"❌ 文档分块失败: {e}")
    exit(1)

# ==========================================
# 步骤3：创建向量嵌入并存入数据库
# ==========================================
print("\n🔢 步骤3：创建向量嵌入（使用本地模型）...")

try:
    # 初始化本地 Embedding 模型
    print("⏳ 正在下载/加载本地 Embedding 模型（首次运行会下载，约400MB）...")
    print("   模型：paraphrase-multilingual-MiniLM-L12-v2")
    print("   特点：支持中文，体积小，速度快")
    
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={'device': 'cpu'},  # 使用CPU，如果有GPU可改为'cuda'
        encode_kwargs={'normalize_embeddings': True}
    )
    
    print("✅ 本地 Embedding 模型加载成功")
    
    # 如果向量库已存在，先删除
    if os.path.exists(VECTOR_STORE_DIR):
        import shutil
        shutil.rmtree(VECTOR_STORE_DIR)
        print("🗑️ 已删除旧的向量库")
    
    # 创建向量数据库
    print("⏳ 正在创建向量数据库...")
    
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=VECTOR_STORE_DIR,
        collection_name="medical_knowledge"
    )
    
    print(f"✅ 向量数据库创建成功！")
    print(f"   - 文档数: {len(documents)}")
    print(f"   - 分块数: {len(splits)}")
    print(f"   - 存储位置: {VECTOR_STORE_DIR}")
    print(f"   - 使用模型: 本地 Sentence Transformers")
    
except Exception as e:
    print(f"❌ 创建向量数据库失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ==========================================
# 步骤4：测试检索
# ==========================================
print("\n🧪 步骤4：测试检索功能...")

try:
    # 测试查询
    test_query = "高血压患者应该注意什么"
    print(f"测试查询：{test_query}")
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    results = retriever.invoke(test_query)
    
    print(f"✅ 检索成功，找到 {len(results)} 个相关文档块：\n")
    
    for i, doc in enumerate(results, 1):
        file_name = os.path.basename(doc.metadata.get("source", "未知"))
        print(f"   {i}. 来源：{file_name}")
        print(f"      内容：{doc.page_content[:100]}...\n")
        
except Exception as e:
    print(f"❌ 测试检索失败: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
print("🎉 知识库构建完成！")
print("=" * 60)
print("\n💡 优势：")
print("   ✅ 完全本地运行，无需API")
print("   ✅ 无配额限制，可以无限使用")
print("   ✅ 支持中文，效果良好")
print("\n下一步：运行 python main.py 启动服务")