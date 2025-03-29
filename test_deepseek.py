import requests
import json

def test_deepseek_api():
    """测试DeepSeek API"""
    print("\n=== 测试 DeepSeek API ===")
    
    # API配置
    api_key = "sk-b9442327e331494dbe25d7c9162bf5c3"  # 替换为你的 API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # 测试文本
    test_text = "贾宝玉和林黛玉是《红楼梦》中的主要人物。"

    # 请求数据
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": f"分析这段文本中的人物关系：{test_text}"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        print("\n1. 尝试API调用...")
        
        # 创建一个 Session 对象，并禁用代理
        session = requests.Session()
        session.trust_env = False  # 忽略系统代理配置
        
        # 发送请求
        response = session.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            proxies=None  # 显式禁用代理
        )
        
        print(f"\n2. 状态码: {response.status_code}")
        print("\n3. API响应:")
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        
        return "API调用成功"

    except Exception as e:
        print("\n错误详情:")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {str(e)}")
        return f"API调用失败: {str(e)}"

if __name__ == "__main__":
    print("=== DeepSeek API 测试 ===")
    result = test_deepseek_api()
    print("\n最终测试结果:", result)