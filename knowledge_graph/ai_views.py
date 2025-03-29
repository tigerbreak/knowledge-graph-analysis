from .services.ai_service import AIService

def generate_from_text(text):
    """从文本生成知识图谱数据"""
    try:
        # 使用AIService进行文本分析
        ai_service = AIService()
        result = ai_service.call_ai_api(text)
        return result
    except Exception as e:
        return {"error": str(e)} 