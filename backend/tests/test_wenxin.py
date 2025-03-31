import os
import django
import logging

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from knowledge_graph.services.wenxin_service import WenxinService

def test_wenxin_service():
    service = WenxinService()
    
    # 测试获取access_token
    logger.info("测试获取access_token...")
    token = service.get_access_token()
    logger.info(f"获取到的token: {token}")
    
    if token:
        # 测试生成思维导图
        content = "这是一篇关于人工智能的文章。人工智能正在改变我们的生活方式，包括机器学习、深度学习、自然语言处理等领域。"
        logger.info("测试生成思维导图...")
        result = service.generate_mindmap(content)
        logger.info(f"生成的思维导图内容: {result}")
    else:
        logger.error("获取token失败，无法测试生成思维导图功能")

if __name__ == '__main__':
    test_wenxin_service() 