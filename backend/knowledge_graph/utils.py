"""
通用工具函数模块
"""
import logging
from typing import Any, Dict, List, Optional
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def format_response(data: Any = None, message: str = 'success', code: int = 0) -> Dict:
    """
    统一响应格式
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 响应代码 (0 表示成功)
        
    Returns:
        dict: 格式化的响应字典
    """
    return {
        'code': code,
        'message': message,
        'data': data
    }


def json_response(data: Any = None, message: str = 'success', code: int = 0, status: int = 200) -> JsonResponse:
    """
    创建 JSON 响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 响应代码
        status: HTTP 状态码
        
    Returns:
        JsonResponse: Django JSON 响应
    """
    return JsonResponse(
        format_response(data, message, code),
        status=status
    )


def error_response(message: str, code: int = 1, status: int = 200) -> JsonResponse:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        code: 错误代码
        status: HTTP 状态码
        
    Returns:
        JsonResponse: Django JSON 响应
    """
    return json_response(data=None, message=message, code=code, status=status)


def validate_file(file, allowed_types: List[str], max_size: int = 10 * 1024 * 1024) -> tuple:
    """
    验证文件
    
    Args:
        file: 上传的文件对象
        allowed_types: 允许的文件扩展名列表
        max_size: 最大文件大小 (字节), 默认 10MB
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not file:
        return False, '文件不能为空'
    
    # 检查文件类型
    file_ext = file.name.split('.')[-1].lower()
    if file_ext not in allowed_types:
        return False, f'不支持的文件格式，请上传以下格式：{", ".join(allowed_types)}'
    
    # 检查文件大小
    if file.size > max_size:
        return False, f'文件大小超过限制 ({max_size / 1024 / 1024:.1f}MB)'
    
    return True, ''


def sanitize_string(text: Optional[str], default: str = '') -> str:
    """
    清理字符串
    
    Args:
        text: 输入文本
        default: 默认值 (当 text 为 None 时)
        
    Returns:
        str: 清理后的字符串
    """
    if text is None:
        return default
    return str(text).strip()


def batch_process(items: List[Any], processor, batch_size: int = 100) -> List[Any]:
    """
    批量处理数据
    
    Args:
        items: 待处理的数据列表
        processor: 处理函数
        batch_size: 每批处理的数量
        
    Returns:
        List[Any]: 处理结果列表
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = processor(batch)
        results.extend(batch_results)
        logger.info(f"已处理 {min(i + batch_size, len(items))}/{len(items)} 项")
    return results


def parse_int(value: Any, default: int = 0) -> int:
    """
    安全地解析整数
    
    Args:
        value: 输入值
        default: 默认值
        
    Returns:
        int: 解析后的整数
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def parse_float(value: Any, default: float = 0.0) -> float:
    """
    安全地解析浮点数
    
    Args:
        value: 输入值
        default: 默认值
        
    Returns:
        float: 解析后的浮点数
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
