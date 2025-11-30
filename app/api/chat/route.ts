import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";
import { ProxyAgent, setGlobalDispatcher } from "undici";

// 定义消息类型
interface Message {
  role: "user" | "assistant";
  content: string;
}

// 配置 undici 全局代理
if (process.env.HTTPS_PROXY || process.env.HTTP_PROXY) {
  const proxyUrl = process.env.HTTPS_PROXY || process.env.HTTP_PROXY;
  console.log("🌐 配置 Undici 代理:", proxyUrl);

  try {
    // 创建 ProxyAgent
    const proxyAgent = new ProxyAgent(proxyUrl);

    // 设置为全局 dispatcher
    setGlobalDispatcher(proxyAgent);

    console.log("✅ Undici 代理已启用");
  } catch (error) {
    console.error("❌ 代理配置失败:", error);
  }
}

// 初始化 Google AI
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY || "");

/**
 * 测试代理连接
 */
async function testProxyConnection() {
  console.log("🧪 测试代理连接...");
  try {
    const response = await fetch("https://www.google.com", {
      method: "HEAD",
      signal: AbortSignal.timeout(5000),
    });
    console.log("✅ 代理测试成功! 状态码:", response.status);
    return true;
  } catch (error) {
    console.error(
      "❌ 代理测试失败:",
      error instanceof Error ? error.message : error
    );
    return false;
  }
}

/**
 * POST /api/chat
 * 处理聊天请求,支持流式响应
 */
export async function POST(req: NextRequest) {
  try {
    console.log("\n================== 新请求开始 ==================");
    console.log("📨 收到聊天请求");

    // 测试代理
    const proxyWorks = await testProxyConnection();
    if (!proxyWorks) {
      console.warn("⚠️ 代理测试失败，但继续尝试 AI 请求");
    }

    const { messages } = await req.json();
    console.log("💬 消息数量:", messages?.length);

    // 验证请求
    if (!messages || !Array.isArray(messages)) {
      console.log("❌ 消息格式错误");
      return NextResponse.json({ error: "消息格式不正确" }, { status: 400 });
    }

    console.log("🤖 初始化 Gemini 模型...");

    // 获取 Gemini 模型 - 平衡速度和质量（推荐）
    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    //     // 快速但质量略低
    // const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
    // // 最高质量但较慢
    // const model = genAI.getGenerativeModel({ model: 'gemini-2.5-pro' });

    // 构建对话历史
    const chat = model.startChat({
      history: messages.slice(0, -1).map((msg: Message) => ({
        role: msg.role === "user" ? "user" : "model",
        parts: [{ text: msg.content }],
      })),
    });

    // 获取最新的用户消息
    const latestMessage = messages[messages.length - 1].content;
    console.log("📤 发送消息到 AI:", latestMessage.substring(0, 50) + "...");

    // 发送消息并获取流式响应
    const result = await chat.sendMessageStream(latestMessage);
    console.log("✅ 开始接收 AI 响应流");

    // 创建流式响应
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of result.stream) {
            const text = chunk.text();
            controller.enqueue(encoder.encode(text));
          }
          controller.close();
          console.log("✅ 响应流传输完成");
          console.log("================== 请求结束 ==================\n");
        } catch (error) {
          console.error("❌ 流式传输错误:", error);
          controller.error(error);
        }
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
      },
    });
  } catch (error) {
    console.error("❌ 聊天 API 错误:", error);

    let errorMessage = "处理请求时出错";
    if (error instanceof Error) {
      errorMessage = error.message;
      console.error("错误详情:", error.message);
    }

    console.log("================== 请求失败 ==================\n");

    return NextResponse.json({ error: errorMessage }, { status: 500 });
  }
}
