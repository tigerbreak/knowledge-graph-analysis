<template>
  <div class="home">
    <el-row :gutter="20">
      <el-col :span="24">
        <h1 class="welcome-title">欢迎使用知识图谱分析系统</h1>
        <p class="welcome-subtitle">基于人工智能的文本分析与知识图谱构建平台</p>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="feature-cards">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" @click="$router.push('/article-analysis')">
          <template #header>
            <div class="card-header">
              <h3>文章分析</h3>
              <el-icon><document /></el-icon>
            </div>
          </template>
          <div class="feature-content">
            <p>上传文章，自动提取关键信息，构建知识网络。支持多种文件格式，智能分析文章内容。</p>
            <ul>
              <li>支持 TXT、PDF、DOCX 格式</li>
              <li>自动提取人物、事件信息</li>
              <li>构建关系网络</li>
              <li>智能内容总结</li>
            </ul>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" @click="$router.push('/knowledge-graph')">
          <template #header>
            <div class="card-header">
              <h3>知识图谱</h3>
              <el-icon><share /></el-icon>
            </div>
          </template>
          <div class="feature-content">
            <p>可视化展示人物关系网络，直观呈现复杂关系。</p>
            <ul>
              <li>交互式关系图谱</li>
              <li>多维度数据展示</li>
              <li>关系路径分析</li>
              <li>图谱数据导出</li>
            </ul>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" @click="$router.push('/character-details')">
          <template #header>
            <div class="card-header">
              <h3>人物档案</h3>
              <el-icon><user /></el-icon>
            </div>
          </template>
          <div class="feature-content">
            <p>详细的人物信息档案，包含人物关系、事件记录等。</p>
            <ul>
              <li>人物基本信息</li>
              <li>关系网络分析</li>
              <li>相关事件追踪</li>
              <li>历史记录查询</li>
            </ul>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="feature-card" @click="$router.push('/events')">
          <template #header>
            <div class="card-header">
              <h3>事件时间线</h3>
              <el-icon><timer /></el-icon>
            </div>
          </template>
          <div class="feature-content">
            <p>按时间顺序展示重要事件，追踪历史发展脉络。</p>
            <ul>
              <li>时间线展示</li>
              <li>事件分类筛选</li>
              <li>关联人物查看</li>
              <li>事件影响分析</li>
            </ul>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { Document, Share, User, Timer } from '@element-plus/icons-vue'

export default {
  name: 'Home',
  components: {
    Document,
    Share,
    User,
    Timer
  }
}
</script>

<style scoped>
.home {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-title {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 10px;
  font-size: 2.5em;
}

.welcome-subtitle {
  text-align: center;
  color: #666;
  margin-bottom: 40px;
  font-size: 1.2em;
}

.feature-cards {
  margin-top: 20px;
}

.feature-card {
  margin-bottom: 20px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #2c3e50;
}

.feature-content {
  color: #666;
}

.feature-content p {
  margin-bottom: 16px;
  line-height: 1.6;
}

.feature-content ul {
  list-style: none;
  padding-left: 0;
}

.feature-content li {
  margin-bottom: 8px;
  padding-left: 20px;
  position: relative;
}

.feature-content li::before {
  content: "•";
  color: #409EFF;
  position: absolute;
  left: 0;
}

.el-icon {
  font-size: 24px;
  color: #409EFF;
}
</style> 