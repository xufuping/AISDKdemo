import { GoogleGenerativeAI } from '@google/generative-ai';
import { NextRequest, NextResponse } from 'next/server';

// 定义消息类型
interface Message {
  role: 'user' | 'assistant';
  content: string;
}

// 初始化 Google AI
const genAI = new GoogleGenerativeAI(process.env.GOOGLE_AI_API_KEY || '');

/**
 * POST /api/chat
 * 处理聊天请求,支持流式响应
 */
export async function POST(req: NextRequest) {
  try {
    console.log('📨 收到请求');

    const { messages } = await req.json();
    console.log('💬 消息内容:', messages);

    // 验证请求
    if (!messages || !Array.isArray(messages)) {
      console.log('❌ 消息格式错误');
      return NextResponse.json(
        { error: '消息格式不正确' },
        { status: 400 }
      );
    }

    console.log('🔑 API Key 存在:', !!process.env.GOOGLE_AI_API_KEY);
    console.log('🔑 API Key 前8位:', process.env.GOOGLE_AI_API_KEY?.substring(0, 8));


    // 获取 Gemini 模型
    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });

    console.log('✅ 模型初始化成功');


    // 构建对话历史
    const chat = model.startChat({
      history: messages.slice(0, -1).map((msg: Message) => ({
        role: msg.role === 'user' ? 'user' : 'model',
        parts: [{ text: msg.content }],
      })),
    });

    // 获取最新的用户消息
    const latestMessage = messages[messages.length - 1].content;

    // 发送消息并获取流式响应
    const result = await chat.sendMessageStream(latestMessage);

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
        } catch (error) {
          console.error('流式传输错误:', error);
          controller.error(error);
        }
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
      },
    });
  } catch (error) {
    console.error('❌ 聊天 API 错误:', error);
    
    return NextResponse.json(
      { error: error instanceof Error ? error.message : '处理请求时出错' },
      { status: 500 }
    );
  }
}