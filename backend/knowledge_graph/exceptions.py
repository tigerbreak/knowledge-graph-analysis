"""
自定义异常类
"""


class KnowledgeGraphError(Exception):
    """知识图谱应用基础异常类"""
    
    def __init__(self, message, code=1):
        self.message = message
        self.code = code
        super().__init__(self.message)


class Neo4jError(KnowledgeGraphError):
    """Neo4j 数据库相关异常"""
    
    def __init__(self, message, code=1001):
        super().__init__(message, code)


class AIAnalysisError(KnowledgeGraphError):
    """AI 分析相关异常"""
    
    def __init__(self, message, code=2001):
        super().__init__(message, code)


class DataValidationError(KnowledgeGraphError):
    """数据验证异常"""
    
    def __init__(self, message, code=3001):
        super().__init__(message, code)


class FileUploadError(KnowledgeGraphError):
    """文件上传异常"""
    
    def __init__(self, message, code=4001):
        super().__init__(message, code)


class NotFoundError(KnowledgeGraphError):
    """资源未找到异常"""
    
    def __init__(self, message, code=404):
        super().__init__(message, code)
