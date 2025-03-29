from django.urls import path
from . import views
from . import graph_views

urlpatterns = [
    # 现有的路由...
    
    # 图谱相关的路由
    path('works/', graph_views.get_works, name='get_works'),
    path('graph/<int:work_id>/', graph_views.get_graph_data, name='get_graph_data'),
    path('node/<int:node_id>/', graph_views.get_node_details, name='get_node_details'),
    path('relationships/<int:node_id>/', graph_views.get_relationships, name='get_relationships'),
] 