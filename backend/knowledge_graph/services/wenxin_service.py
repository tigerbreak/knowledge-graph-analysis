import requests
import logging
import json
from django.conf import settings
import os

logger = logging.getLogger(__name__)

# 禁用所有代理设置
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''

class WenxinService:
    def __init__(self):
        self.api_key = settings.WENXIN_API_KEY
        self.secret_key = settings.WENXIN_SECRET_KEY
        self.access_token = None

    def get_access_token(self):
        """获取文心一言access_token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            logger.info(f"正在获取access_token，API_KEY: {self.api_key[:8]}...")
            session = requests.Session()
            session.trust_env = False  # 禁用环境代理
            session.verify = True  # 启用SSL验证
            session.proxies.clear()  # 清除所有代理设置
            
            response = session.post(url, params=params)
            result = response.json()
            if 'access_token' in result:
                self.access_token = result['access_token']
                logger.info("成功获取access_token")
                return self.access_token
            else:
                logger.error(f"获取access_token失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取access_token异常: {str(e)}", exc_info=True)
            return None

    def generate_mindmap(self, content):
        """生成思维导图的markdown文本"""
        if not self.access_token:
            self.get_access_token()
            if not self.access_token:
                return None

        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token={self.access_token}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        prompt = """请分析这篇文章，生成markdown格式的思维导图结构。要求：
1. 提取文章的主要内容、核心观点、关键人物、重要情节等
2. 使用markdown标准语法，用#表示标题层级
3. 结构要清晰，层次分明
4. 重点突出，逻辑合理
5. 使用短语或简单句概括内容

示例格式：
# 文章标题
## 核心内容
### 主要观点1
- 观点描述
### 主要观点2
- 观点描述
## 人物分析
### 主要人物
- 人物特点
### 次要人物
- 人物特点
## 情节发展
### 开篇
- 情节概述
### 高潮
- 情节概述
### 结局
- 情节概述
"""

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": prompt + "\n\n需要分析的文章内容：\n" + content
                }
            ],
            "temperature": 0.95,
            "top_p": 0.8,
            "penalty_score": 1,
            "enable_system_memory": False,
            "disable_search": False,
            "enable_citation": False
        }
        
        try:
            logger.info("正在调用文心一言API生成思维导图")
            session = requests.Session()
            session.trust_env = False  # 禁用环境代理
            session.verify = True  # 启用SSL验证
            session.proxies.clear()  # 清除所有代理设置
            
            response = session.post(url, headers=headers, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"))
            result = response.json()
            
            if 'result' in result:
                logger.info("成功生成思维导图")
                return result['result']
            else:
                logger.error(f"生成思维导图失败，API返回: {result}")
                return None
                
        except Exception as e:
            logger.error(f"调用文心一言API异常: {str(e)}", exc_info=True)
            return None 