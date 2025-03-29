from django.core.management.base import BaseCommand
from knowledge_graph.models import Character, Relationship

class Command(BaseCommand):
    help = '修正人物来源信息'

    def handle(self, *args, **options):
        # 三国人物列表
        three_kingdoms_characters = ['刘备', '关羽', '张飞', '诸葛亮']
        
        # 更新三国人物的来源
        updated_count = Character.objects.filter(name__in=three_kingdoms_characters).update(source='三国演义')
        
        self.stdout.write(f'已更新 {updated_count} 个三国人物的来源')
        
        # 更新关系的source_text
        relationships = Relationship.objects.filter(
            source__name__in=three_kingdoms_characters) | Relationship.objects.filter(
            target__name__in=three_kingdoms_characters)
        
        for rel in relationships:
            rel.source_text = '三国演义'
            rel.save()
            
        self.stdout.write(f'已更新 {relationships.count()} 个关系的来源')
        
        # 删除跨作品关系
        cleaned_count = 0
        for rel in Relationship.objects.all():
            if (rel.source.source != rel.target.source or 
                rel.source.source != rel.source_text or 
                rel.target.source != rel.source_text):
                self.stdout.write(f'删除错误关系: {rel.source.name}({rel.source.source}) -> {rel.target.name}({rel.target.source})')
                rel.delete()
                cleaned_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'清理完成，共删除 {cleaned_count} 个错误关系')) 