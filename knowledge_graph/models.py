from django.db import models
from django.db.models import JSONField
from django.utils import timezone

# Create your models here.

class Work(models.Model):
    """作品模型"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_graph_work'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Article(models.Model):
    """文章模型"""
    title = models.CharField(max_length=200)
    content = models.TextField(default='')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_graph_article'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Event(models.Model):
    """事件模型"""
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True, default='')
    time = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    participants = models.TextField(null=True, blank=True, default='')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='events')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='events', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_graph_event'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Character(models.Model):
    """人物模型"""
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True, default='')
    faction = models.CharField(max_length=100, null=True, blank=True)
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='characters')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_graph_character'
        ordering = ['-created_at']
        unique_together = ('name', 'work')

    def __str__(self):
        return self.name

class Relationship(models.Model):
    """关系模型"""
    source = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='relationships_as_source')
    target = models.ForeignKey(Character, on_delete=models.CASCADE, related_name='relationships_as_target')
    type = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True, default='')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='relationships')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_graph_relationship'
        ordering = ['-created_at']
        unique_together = ('source', 'target', 'type', 'work')

    def __str__(self):
        return f"{self.source.name} -> {self.target.name} ({self.type})"

class Faction(models.Model):
    """势力模型"""
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True, default='')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, related_name='factions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'knowledge_graph_faction'
        ordering = ['-created_at']
        unique_together = ('name', 'work')

    def __str__(self):
        return self.name

class AnalysisResult(models.Model):
    """分析结果模型"""
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name='文章')
    result = models.JSONField('分析结果')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '分析结果'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.article.title}的分析结果"
