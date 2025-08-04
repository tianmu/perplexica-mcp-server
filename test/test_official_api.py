"""按照官方文档测试Perplexica API"""
import asyncio
import httpx
import json

async def test_official_api():
    """按照官方文档测试/api/search接口"""
    print("🧪 按照官方文档测试Perplexica API")
    print("=" * 50)
    
    # 按照官方文档的请求体结构
    official_request = {
        "chatModel": {
            "provider": "custom_openai",
            "customOpenAIBaseURL":"https://api.poe.com/v1",
            "customOpenAIKey":"your_api_key",
            "name": "gpt-4.1"  # 注意：官方文档用的是 'name' 不是 'model'
        },
        "embeddingModel": {
            "provider": "transformers", 
            "name": "xenova-bge-small-en-v1.5"  # 注意：官方文档用的是 'name'
        },
        "optimizationMode": "speed",
        "focusMode": "webSearch",
        "query": "What is Perplexica",
        "history": [
            ["human", "Hi, how are you?"],
            ["assistant", "I am doing well, how can I help you today?"]
        ],
        "systemInstructions": "Focus on providing technical details about Perplexica's architecture.",
        "stream": False
    }
    
    print("📋 测试请求体:")
    print(json.dumps(official_request, indent=2, ensure_ascii=False))
    print()
    
    client = httpx.AsyncClient(timeout=30.0)
    
    try:
        print("🚀 发送请求到 /api/search...")
        response = await client.post(
            "http://localhost:3000/api/search",
            json=official_request,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 请求成功!")
            
            response_data = response.json()
            print(f"💬 消息长度: {len(response_data.get('message', ''))}")
            print(f"📚 来源数量: {len(response_data.get('sources', []))}")
            
            # 显示部分响应内容
            message = response_data.get('message', '')
            if len(message) > 200:
                print(f"📄 消息预览: {message[:200]}...")
            else:
                print(f"📄 完整消息: {message}")
                
            # 显示来源信息
            sources = response_data.get('sources', [])
            if sources:
                print(f"\n📚 前几个来源:")
                for i, source in enumerate(sources[:3]):
                    title = source.get('metadata', {}).get('title', '无标题')
                    url = source.get('metadata', {}).get('url', '无URL')
                    print(f"   {i+1}. {title}")
                    print(f"      URL: {url}")
            
        else:
            print(f"❌ 请求失败: HTTP {response.status_code}")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
    
    finally:
        await client.aclose()
    
   

if __name__ == "__main__":
    asyncio.run(test_official_api())