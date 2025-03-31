import requests
import json

url = "http://localhost:8000/api/mindmap/test/"
headers = {"Content-Type": "application/json"}
data = {
    "content": "这是一篇关于人工智能的文章。人工智能正在改变我们的生活方式，包括机器学习、深度学习、自然语言处理等领域。"
}

response = requests.post(url, headers=headers, json=data)
print("状态码:", response.status_code)
print("响应内容:", response.text) 