"""
事件相关的视图模块
包含事件列表、详情等功能
"""
import logging
from django.http import JsonResponse
from rest_framework.decorators import api_view

from ..models import Event, Work

logger = logging.getLogger(__name__)


def get_mysql_works():
    """从 MySQL 获取作品列表"""
    try:
        works = Work.objects.all().values('id', 'name')
        return list(works)
    except Exception as e:
        logger.error(f"获取作品列表失败：{str(e)}", exc_info=True)
        return []


@api_view(['GET'])
def get_events(request, work_id=None):
    """
    获取事件列表
    
    Args:
        work_id: 作品 ID (可选)
        
    Returns:
        JsonResponse: 事件列表和作品列表
    """
    try:
        works_list = get_mysql_works()
        
        filters = {}
        if work_id:
            filters['work_id'] = work_id
        
        events = Event.objects.filter(**filters).values(
            'id', 'name', 'time', 'description', 'location', 'participants'
        )
        
        events_list = []
        for event in events:
            event_data = {
                'id': event['id'],
                'title': event['name'],
                'time': event['time'],
                'description': event['description'],
                'location': event['location'],
                'participants': event['participants'].split(',') if event['participants'] else []
            }
            events_list.append(event_data)
        
        logger.info(f"从 MySQL 获取到 {len(events_list)} 个事件")
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'events': events_list,
                'works': works_list
            }
        })
        
    except Exception as e:
        logger.error(f"获取事件列表失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取事件列表失败：{str(e)}'
        })


@api_view(['GET'])
def event_detail(request, event_id):
    """
    获取事件详情
    
    Args:
        event_id: 事件 ID
        
    Returns:
        JsonResponse: 事件详情
    """
    try:
        event = Event.objects.select_related('work', 'article').get(id=event_id)
        
        event_data = {
            'id': event.id,
            'name': event.name,
            'description': event.description or '',
            'time': event.time or '',
            'location': event.location or '',
            'participants': event.participants.split(',') if event.participants else [],
            'work_id': event.work.id if event.work else None,
            'work_name': event.work.name if event.work else '',
            'article_id': event.article.id if event.article else None,
            'article_title': event.article.title if event.article else '',
            'created_at': event.created_at.isoformat(),
            'updated_at': event.updated_at.isoformat()
        }
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': event_data
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'code': 1,
            'message': '事件不存在'
        }, status=404)
    except Exception as e:
        logger.error(f"获取事件详情失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取事件详情失败：{str(e)}'
        })


@api_view(['GET'])
def event_list(request):
    """
    获取事件列表 (支持过滤和搜索)
    
    Query Parameters:
        - work_id: 作品 ID (可选)
        - search: 搜索关键词 (可选)
        
    Returns:
        JsonResponse: 事件列表
    """
    try:
        work_id = request.GET.get('work_id')
        search = request.GET.get('search', '')
        
        filters = {}
        if work_id:
            filters['work_id'] = work_id
        if search:
            filters['name__icontains'] = search
        
        events = Event.objects.filter(**filters).select_related('work').order_by('-created_at')
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'name': event.name,
                'time': event.time or '',
                'location': event.location or '',
                'work_id': event.work.id if event.work else None,
                'work_name': event.work.name if event.work else '',
                'created_at': event.created_at.isoformat()
            })
        
        return JsonResponse({
            'code': 0,
            'message': 'success',
            'data': {
                'events': events_data,
                'total': len(events_data)
            }
        })
        
    except Exception as e:
        logger.error(f"获取事件列表失败：{str(e)}", exc_info=True)
        return JsonResponse({
            'code': 1,
            'message': f'获取事件列表失败：{str(e)}'
        })
