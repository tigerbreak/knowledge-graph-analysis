"""
知识图谱应用 URL 配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    article_views,
    character_views,
    work_views,
    event_views,
    admin_views
)

# API 路由器
router = DefaultRouter()
router.register(r'relationships', article_views.RelationshipViewSet)

urlpatterns = [
    # 文章相关
    path('upload/', article_views.upload_file, name='upload-file'),
    path('articles/', article_views.article_list, name='article-list'),
    path('articles/<int:article_id>/', article_views.article_detail, name='article-detail'),
    path('articles/<int:article_id>/analysis/', article_views.article_analysis, name='article-analysis'),
    path('analysis-history/', article_views.get_analysis_history, name='analysis-history'),
    
    # 人物相关
    path('characters/', character_views.character_list, name='character-list'),
    path('characters/details/', character_views.character_details, name='character-details'),
    path('characters/<str:character_name>/relationships/', character_views.character_relationships, name='character-relationships'),
    
    # 作品相关
    path('works/', work_views.work_list, name='work-list'),
    path('works/<int:work_id>/graph/', work_views.get_work_graph, name='work-graph'),
    path('works/sync/', work_views.sync_works, name='sync-works'),
    path('works/clean-duplicates/', work_views.clean_duplicate_works, name='clean-duplicate-works'),
    path('works/check-data/', work_views.check_work_data, name='check-work-data'),
    
    # 图谱数据
    path('graph/', work_views.get_graph_data, name='graph-data'),
    path('graph/<int:work_id>/', work_views.get_graph_data, name='graph-data-by-work'),
    path('graph/node/<str:node_id>/', work_views.get_node_details, name='node-details'),
    
    # 事件相关
    path('events/', event_views.event_list, name='event-list'),
    path('events/<int:event_id>/', event_views.event_detail, name='event-detail'),
    path('works/<int:work_id>/events/', event_views.get_events, name='work-events'),
    
    # 管理相关
    path('admin/clean-graph/', admin_views.clean_graph_data, name='clean-graph'),
    path('admin/delete-article/<int:article_id>/', admin_views.delete_article, name='delete-article'),
    path('admin/clean-test-data/', admin_views.clean_test_data, name='clean-test-data'),
    path('admin/test-relationships/<int:work_id>/', admin_views.test_relationships, name='test-relationships'),
    path('admin/debug-database/', admin_views.debug_database, name='debug-database'),
    path('admin/check-relationships/', admin_views.check_relationships, name='check-relationships'),
    path('admin/clear-database/', admin_views.clear_database, name='clear-database'),
    
    # 包含路由器注册的 URL
    path('', include(router.urls)),
]
