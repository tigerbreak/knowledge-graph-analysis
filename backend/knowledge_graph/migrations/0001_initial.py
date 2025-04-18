# Generated by Django 4.2.20 on 2025-03-22 07:10

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='姓名')),
                ('faction', models.CharField(blank=True, max_length=100, null=True, verbose_name='势力')),
                ('birthplace', models.CharField(blank=True, max_length=100, null=True, verbose_name='出生地')),
                ('bio', models.TextField(blank=True, null=True, verbose_name='简介')),
            ],
            options={
                'verbose_name': '人物',
                'verbose_name_plural': '人物',
            },
        ),
        migrations.CreateModel(
            name='Work',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='名称')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '作品',
                'verbose_name_plural': '作品',
            },
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relationship_type', models.CharField(max_length=100, verbose_name='关系类型')),
                ('description', models.TextField(blank=True, null=True, verbose_name='描述')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relationships_as_source', to='knowledge_graph.character', verbose_name='源角色')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='relationships_as_target', to='knowledge_graph.character', verbose_name='目标角色')),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_graph.work', verbose_name='作品')),
            ],
            options={
                'verbose_name': '关系',
                'verbose_name_plural': '关系',
            },
        ),
        migrations.CreateModel(
            name='Faction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='名称')),
                ('leader', models.CharField(blank=True, max_length=100, null=True, verbose_name='领袖')),
                ('region', models.CharField(blank=True, max_length=100, null=True, verbose_name='地区')),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_graph.work', verbose_name='作品')),
            ],
            options={
                'verbose_name': '势力',
                'verbose_name_plural': '势力',
            },
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='名称')),
                ('time', models.CharField(blank=True, max_length=100, null=True, verbose_name='时间')),
                ('description', models.TextField(blank=True, null=True, verbose_name='描述')),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_graph.work', verbose_name='作品')),
            ],
            options={
                'verbose_name': '事件',
                'verbose_name_plural': '事件',
            },
        ),
        migrations.AddField(
            model_name='character',
            name='work',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_graph.work', verbose_name='作品'),
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='标题')),
                ('text', models.TextField(verbose_name='内容')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('work', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='articles', to='knowledge_graph.work', verbose_name='作品')),
            ],
            options={
                'verbose_name': '文章',
                'verbose_name_plural': '文章',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AnalysisResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result', models.JSONField(verbose_name='分析结果')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('article', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='knowledge_graph.article', verbose_name='文章')),
            ],
            options={
                'verbose_name': '分析结果',
                'verbose_name_plural': '分析结果',
            },
        ),
    ]
