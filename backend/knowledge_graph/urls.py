from django.urls import path
from . import views

urlpatterns = [
    # 文章相关
    path('article/list/', views.article_list, name='article_list'),
    path('article/<int:article_id>/', views.article_detail, name='article_detail'),
    path('article/analyze/', views.analyze_article, name='analyze_article'),
    path('article/<int:article_id>/analysis/', views.article_analysis, name='article_analysis'),
    path('article/<int:article_id>/delete/', views.delete_article, name='delete_article'),
    path('article/<int:article_id>/graph/', views.get_article_graph_data, name='article_graph'),
    path('article/upload/', views.upload_file, name='upload_file'),
    
    # 作品相关
    path('works/', views.work_list, name='work_list'),
    path('work/<int:work_id>/graph/', views.get_work_graph, name='work_graph'),
    
    # 人物详情
    path('character-details/', views.character_details, name='character_details'),
    
    # 知识图谱相关
    path('node/<int:node_id>/', views.get_node_details, name='node_details'),
    
    path('graph/', views.get_graph_data, name='get_graph_data'),
    path('graph/<int:work_id>/', views.get_graph_data, name='get_work_graph_data'),
    path('graph/clean/', views.clean_graph_data, name='clean_graph_data'),

    # 测试页面
    path('test_relationships/<int:work_id>/', views.test_relationships, name='test_relationships'),

    path('debug_database/', views.debug_database, name='debug_database'),
    path('check_relationships/', views.check_relationships, name='check_relationships'),
    path('clear_database/', views.clear_database, name='clear_database'),

    path('clean-duplicate-works/', views.clean_duplicate_works, name='clean_duplicate_works'),

    path('check-work-data/', views.check_work_data, name='check_work_data'),

    path('sync-works/', views.sync_works, name='sync_works'),

    path('events/', views.get_events, name='get_events'),
    path('events/<int:work_id>/', views.get_events, name='get_work_events'),
] 