# 医学知识问答系统 🏥

这是一个智能的医学知识问答系统，可以帮助用户查询医学健康相关的问题。系统使用了 AI 技术，能够从知识库中检索信息并给出专业的回答。

## 📖 项目简介

本项目是一个基于 **RAG（检索增强生成）** 技术的垂直领域问答机器人：

- **前端**：使用 Next.js 构建，提供友好的聊天界面
- **后端**：使用 Python FastAPI 构建，提供 AI 问答服务
- **AI 模型**：使用 Google Gemini 生成回答
- **知识库**：包含健康体检、常见药物、心血管疾病、糖尿病、高血压等医学文档
- **智能检索**：自动从知识库中查找相关信息，提供准确的回答

## 🎯 主要功能

✅ **智能问答**：基于医学知识库的专业问答  
✅ **流式响应**：实时显示 AI 回答内容  
✅ **来源追溯**：显示回答内容的知识来源  
✅ **上下文理解**：支持多轮对话，记住对话历史  
✅ **本地化部署**：所有数据存储在本地，保护隐私

## 🛠️ 技术栈

### 前端技术
- **Next.js 16**：React 框架，用于构建用户界面
- **TypeScript**：JavaScript 的超集，提供类型检查
- **TailwindCSS**：CSS 框架，用于样式设计
- **React Markdown**：渲染 Markdown 格式的回答

### 后端技术
- **FastAPI**：现代化的 Python Web 框架
- **LangChain**：AI 应用开发框架
- **ChromaDB**：向量数据库，存储文档向量
- **Sentence Transformers**：本地嵌入模型
- **Google Gemini**：Google 的 AI 大语言模型

## 📋 开始之前的准备

### 1. 系统要求

- **操作系统**：Windows、macOS 或 Linux
- **Python**：3.13
- **Node.js**：18 或以上版本
- **pnpm**：包管理工具（推荐）或 npm

### 2. 获取 Google AI API Key

本项目使用 Google Gemini API，需要先获取 API Key：

1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
2. 登录你的 Google 账号
3. 点击 "Create API Key" 创建 API Key
4. 复制生成的 API Key（后面会用到）

> 💡 **提示**：Google AI 提供免费额度，对于学习和小型项目足够使用

### 3. 检查环境

打开终端（命令行），运行以下命令检查环境：
```
# 检查 Python 版本（应该是 3.10 或以上, 建议3.13）
python --version
# 或者
python3 --version

# 检查 Node.js 版本（应该是 18 或以上）
node --version

# 检查 pnpm（如果没有，可以用 npm 代替）
pnpm --version如果提示"命令不存在"，说明需要先安装对应的软件。
```

## 🚀 安装步骤

### 第一步：下载项目

如果你还没有项目文件，先下载或克隆项目：

# 从 Git 克隆
```
git clone <项目地址>
```

# 如果已经有项目文件，直接进入项目目录
```
cd my-ai-demo
```

###第二步：配置环境变量

1. 在项目根目录创建一个名为 `.env.local` 的文件（注意，这是一个隐藏文件）, 文件中添加以下内容：
```
GOOGLE_AI_API_KEY=AIzaSyC9GNDuGbQSQzHt7l3VK5AIkxZ_Qw3OA8I
HTTPS_PROXY=http://127.0.0.1:7890
HTTP_PROXY=http://127.0.0.1:7890
```


2. 创建 `backend/.env` 文件，文件中添加以下内容：
```
# Google AI API Key
GOOGLE_AI_API_KEY=<你的API key>

# 如果需要代理
HTTP_PROXY=http://127.0.0.1:7890
HTTPS_PROXY=http://127.0.0.1:7890

# 服务配置
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### 第三步：安装前端依赖并启动前端
```
在项目根目录运行：

# 使用 pnpm（推荐）
pnpm install

# 或使用 npm - 这个过程会下载前端所需的所有依赖包，可能需要几分钟时间。
npm install

安装完成之后，启动服务，访问 http://localhost:3000/

# 使用 pnpm
pnpm dev

# 或使用 npm
npm run dev
```

### 第四步：安装后端依赖
```
1. 进入后端目录：

cd backend

2. 创建 Python 虚拟环境（推荐，但不是必须）：

# macOS/Linux
python3 -m venv myenv
source myenv/bin/activate

# Windows
python -m venv myenv
myenv\Scripts\activate看到命令提示符前面出现 `(myenv)` 说明虚拟环境已激活。

3. 安装 Python 依赖：
pip install -r requirements.txt

这个过程会下载后端所需的所有 Python 包，可能需要较长时间（特别是第一次安装）。

> 💡 **下载慢的解决办法**：如果下载很慢，可以使用国内镜像源：
>
> pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

 ### 第五步：构建知识库（重要！）

在 backend 目录下运行：`python load_documents.py`这个脚本会：

- 读取 `data/txt/` 目录下的所有医学文档
- 将文档分割成小块
- 生成向量（数字表示）
- 存储到向量数据库中

```
### 添加新的知识文档

1. 将 `.txt` 格式的文档放入 `backend/data/txt/` 目录
2. 重新运行：`python load_documents.py`
3. 重启后端服务
```

### 第六步，启动后端（Python）
确保在 backend 目录下,如果使用了虚拟环境，确保已激活（命令提示符前有 (myenv)）,运行：`python main.py`

看到以下信息说明后端启动成功：
```
🚀 启动医学知识问答系统后端
📍 地址: http://0.0.0.0:8000
📖 API文档: http://0.0.0.0:8000/docs
📚 知识库: 已加载 ✅
```



