from django.core.management.base import BaseCommand
from knowledge_graph.models import Character, Relationship, Event

class Command(BaseCommand):
    help = '清空所有人物、关系和事件数据'

    def handle(self, *args, **options):
        self.stdout.write('开始清空数据...')
        
        # 删除所有关系
        rel_count = Relationship.objects.all().count()
        Relationship.objects.all().delete()
        self.stdout.write(f'已删除 {rel_count} 条关系数据')
        
        # 删除所有事件
        event_count = Event.objects.all().count()
        Event.objects.all().delete()
        self.stdout.write(f'已删除 {event_count} 个事件数据')
        
        # 删除所有人物
        char_count = Character.objects.all().count()
        Character.objects.all().delete()
        self.stdout.write(f'已删除 {char_count} 个人物数据')
        
        self.stdout.write(self.style.SUCCESS('所有数据已清空')) 