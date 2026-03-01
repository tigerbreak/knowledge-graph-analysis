"""
AI 服务模块
提供文章分析、AI 调用等功能
"""
import logging
import json
import requests
from typing import Dict, List, Optional, Any
from django.conf import settings

from .exceptions import AIAnalysisError

logger = logging.getLogger(__name__)


class AIService:
    """AI 分析服务类"""
    
    def __init__(self):
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.api_key = settings.DEEPSEEK_API_KEY
        self.timeout = settings.DEEPSEEK_API_TIMEOUT
        self.chunk_size = settings.DEEPSEEK_CHUNK_SIZE
        self.max_retries = 3
        
        self.system_prompt = """你是一个文学作品分析专家。请分析以下文章内容，识别出:
    1. 文章所属的作品名称
    2. 文章标题（根据内容总结，15 字以内）
    3. 文章中的人物、势力、事件和关系信息

    请以 JSON 格式返回分析结果：
    {
        "work_name": "作品名称",
        "title": "文章标题",
        "characters": [
            {
                "name": "人物名",
                "description": "人物描述",
                "faction": "所属势力"
            }
        ],
        "forces": [
            {
                "name": "势力名",
                "description": "描述"
            }
        ],
        "events": [
            {
                "title": "事件标题",
                "description": "事件描述",
                "participants": ["参与者 1", "参与者 2"],
                "location": "发生地点",
                "time": "发生时间"
            }
        ],
        "relationships": [
            {
                "source": "来源人物",
                "target": "目标人物/势力",
                "type": "关系类型",
                "description": "关系描述"
            }
        ]
    }

    关系类型说明：
    - 人物间关系：monarch-minister(君臣)、master-apprentice(师徒)、friend(朋友)、enemy(敌人)、family(家人)、spouse(配偶)
    - 人物与势力关系：belongs_to(属于)、leads(领导)、affiliated(附属)、opposes(对立)

    要求：
    1. 关系要双向记录，比如 A 是 B 的君主，要同时记录 B 是 A 的臣子
    2. 势力关系要准确，一个人物可以同时属于多个势力
    3. 事件要包含所有相关人物和具体地点
    4. 时间信息如果模糊也要记录，如"某年冬天"
    5. 所有描述要简明扼要
    6. 请确保返回的是合法的 JSON 格式，不要包含任何其他文本
    """
    
    def _create_session(self) -> requests.Session:
        """创建请求会话"""
        session = requests.Session()
        session.trust_env = False
        session.proxies = {
            "http": None,
            "https": None
        }
        return session
    
    def _parse_ai_response(self, content: str) -> Optional[Dict]:
        """
        解析 AI 返回的 JSON 内容
        
        Args:
            content: AI 返回的原始文本
            
        Returns:
            Optional[Dict]: 解析后的字典，失败返回 None
        """
        try:
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            elif content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败：{content[:200]}...")
            logger.error(f"错误详情：{str(e)}")
            return None
    
    def _normalize_analysis(self, analysis: Dict) -> Dict:
        """
        规范化分析结果数据
        
        Args:
            analysis: 原始分析结果
            
        Returns:
            Dict: 规范化后的分析结果
        """
        normalized = {
            "work_name": "",
            "title": "",
            "characters": [],
            "forces": [],
            "events": [],
            "relationships": []
        }
        
        # 规范化人物数据
        for char in analysis.get('characters', []):
            normalized['characters'].append({
                'name': char.get('name', ''),
                'description': char.get('description', ''),
                'faction': char.get('faction', '')
            })
        
        # 规范化势力数据
        for force in analysis.get('forces', []):
            normalized['forces'].append({
                'name': force.get('name', ''),
                'description': force.get('description', '')
            })
        
        # 规范化事件数据
        for event in analysis.get('events', []):
            participants = event.get('participants', [])
            if not isinstance(participants, list):
                participants = []
            
            normalized['events'].append({
                'title': event.get('title', ''),
                'description': event.get('description', ''),
                'location': event.get('location', ''),
                'time': event.get('time', ''),
                'participants': participants
            })
        
        # 规范化关系数据
        for rel in analysis.get('relationships', []):
            normalized['relationships'].append({
                'source': rel.get('source', ''),
                'target': rel.get('target', ''),
                'type': rel.get('type', '').lower(),
                'description': rel.get('description', '')
            })
        
        # 复制基本信息
        if analysis.get("work_name"):
            normalized["work_name"] = analysis["work_name"]
        if analysis.get("title"):
            normalized["title"] = analysis["title"]
        
        return normalized
    
    def _deduplicate_results(self, results: Dict) -> Dict:
        """
        对分析结果进行去重
        
        Args:
            results: 分析结果
            
        Returns:
            Dict: 去重后的结果
        """
        # 人物去重
        seen_chars = set()
        unique_chars = []
        for char in results.get("characters", []):
            if char.get("name") and char["name"] not in seen_chars:
                seen_chars.add(char["name"])
                unique_chars.append(char)
        results["characters"] = unique_chars
        
        # 势力去重
        seen_forces = set()
        unique_forces = []
        for force in results.get("forces", []):
            if force.get("name") and force["name"] not in seen_forces:
                seen_forces.add(force["name"])
                unique_forces.append(force)
        results["forces"] = unique_forces
        
        return results
    
    def analyze_article(self, content: str) -> Dict:
        """
        分析文章内容
        
        Args:
            content: 文章内容
            
        Returns:
            Dict: 分析结果
            
        Raises:
            AIAnalysisError: 分析失败时抛出
        """
        session = self._create_session()
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # 分块处理长文本
                content_chunks = [
                    content[i:i+self.chunk_size] 
                    for i in range(0, len(content), self.chunk_size)
                ]
                
                combined_analysis = {
                    "work_name": "",
                    "title": "",
                    "characters": [],
                    "forces": [],
                    "events": [],
                    "relationships": []
                }
                
                for chunk in content_chunks:
                    data = {
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": chunk}
                        ],
                        "model": "deepseek-chat",
                        "temperature": 0.1,
                        "max_tokens": 2000,
                        "stream": False
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    response = session.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=self.timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        ai_content = result['choices'][0]['message']['content']
                        
                        analysis = self._parse_ai_response(ai_content)
                        if analysis:
                            normalized = self._normalize_analysis(analysis)
                            
                            # 合并分析结果
                            if not combined_analysis["work_name"] and normalized["work_name"]:
                                combined_analysis["work_name"] = normalized["work_name"]
                            if not combined_analysis["title"] and normalized["title"]:
                                combined_analysis["title"] = normalized["title"]
                            combined_analysis["characters"].extend(normalized["characters"])
                            combined_analysis["forces"].extend(normalized["forces"])
                            combined_analysis["events"].extend(normalized["events"])
                            combined_analysis["relationships"].extend(normalized["relationships"])
                    else:
                        response.raise_for_status()
                
                # 去重处理
                self._deduplicate_results(combined_analysis)
                
                return combined_analysis
                
            except Exception as e:
                retry_count += 1
                logger.error(f"AI API 调用失败 (尝试 {retry_count}/{self.max_retries}): {str(e)}")
                if retry_count >= self.max_retries:
                    logger.error("AI API 调用失败，已达最大重试次数")
                    raise AIAnalysisError(f"AI 分析失败：{str(e)}")
        
        raise AIAnalysisError("AI 分析失败：未知错误")


# 全局服务实例
ai_service = AIService()