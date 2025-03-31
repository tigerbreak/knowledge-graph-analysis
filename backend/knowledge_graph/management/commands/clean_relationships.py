from django.core.management.base import BaseCommand
from knowledge_graph.models import Relationship

class Command(BaseCommand):
    help = '清理错误的跨作品人物关系'

    def handle(self, *args, **options):
        # 获取所有关系
        relationships = Relationship.objects.all()
        cleaned_count = 0
        
        self.stdout.write('开始清理跨作品关系...')
        
        for rel in relationships:
            # 如果源人物和目标人物的来源不同，或者与关系的来源不同，则删除该关系
            if (rel.source.source != rel.target.source or 
                rel.source.source != rel.source_text or 
                rel.target.source != rel.source_text):
                self.stdout.write(f'删除错误关系: {rel.source.name}({rel.source.source}) -> {rel.target.name}({rel.target.source})')
                rel.delete()
                cleaned_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'清理完成，共删除 {cleaned_count} 个错误关系')) 