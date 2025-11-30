// test-api-key.mjs
import { ProxyAgent, setGlobalDispatcher } from 'undici';

const API_KEY = 'AIzaSyC9GNDuGbQSQzHt7l3VK5AIkxZ_Qw3OA8I';

console.log('🔑 测试 API Key:', API_KEY.substring(0, 20) + '...');
console.log('');

// 配置 undici 代理
const proxyUrl = 'http://127.0.0.1:7890';
console.log('🌐 配置 Undici 代理:', proxyUrl);

try {
  const proxyAgent = new ProxyAgent(proxyUrl);
  setGlobalDispatcher(proxyAgent);
  console.log('✅ 代理已启用\n');
} catch (error) {
  console.error('❌ 代理配置失败:', error.message);
  process.exit(1);
}

console.log('📡 通过代理请求可用模型列表...\n');

try {
  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models?key=${API_KEY}`,
    {
      signal: AbortSignal.timeout(10000), // 10秒超时
    }
  );
  
  if (!response.ok) {
    console.error('❌ 请求失败:', response.status, response.statusText);
    const text = await response.text();
    console.error('错误详情:', text);
    process.exit(1);
  }
  
  const data = await response.json();
  
  console.log('✅ 请求成功！');
  console.log('📋 你可以使用的模型：\n');
  
  if (data.models && data.models.length > 0) {
    data.models.forEach((model, index) => {
      console.log(`${index + 1}. ${model.name}`);
      console.log(`   显示名: ${model.displayName}`);
      console.log(`   版本: ${model.version || '默认'}`);
      console.log(`   支持的方法: ${model.supportedGenerationMethods?.join(', ') || '无'}`);
      console.log('');
    });
    
    console.log('\n💡 使用建议：');
    console.log('在 route.ts 中使用上面列表中的任意一个模型名称');
    console.log('例如: genAI.getGenerativeModel({ model: "' + data.models[0].name.replace('models/', '') + '" })');
  } else {
    console.log('⚠️ 没有可用的模型');
    console.log('这可能意味着：');
    console.log('1. API Key 无效或已过期');
    console.log('2. 账号未激活 Generative Language API');
    console.log('3. 地区限制（中国账号可能受限）');
  }
  
} catch (error) {
  console.error('❌ 发生错误:', error.message);
  console.error('\n可能的原因：');
  console.error('1. Clash 代理未运行或端口不是 7890');
  console.error('2. 网络连接问题');
  console.error('3. Google API 服务不可用');
  console.error('\n调试建议：');
  console.error('先测试代理: curl -x http://127.0.0.1:7890 https://www.google.com -I');
}