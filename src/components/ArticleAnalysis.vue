<template>
  <div class="container">
    <!-- 导航栏 -->
    <nav class="nav-bar">
      <div class="nav-brand">知识图谱分析系统</div>
      <div class="nav-menu">
        <router-link to="/" class="nav-item">首页</router-link>
        <router-link to="/article-analysis" class="nav-item active">文章分析</router-link>
        <router-link to="/character-network" class="nav-item">人物关系图谱</router-link>
        <router-link to="/character-info" class="nav-item">人物评价</router-link>
        <router-link to="/event-timeline" class="nav-item">事件列表</router-link>
        <router-link to="/force-distribution" class="nav-item">势力分布</router-link>
    </div>
    </nav>

    <div class="main-content">
      <div class="left-panel">
        <div class="view-controls" v-if="currentArticle">
          <el-radio-group v-model="viewMode" size="large">
            <el-radio-button label="table">表格模式</el-radio-button>
            <el-radio-button label="graph">知识图谱</el-radio-button>
          </el-radio-group>
        </div>

        <div v-if="viewMode === 'table' && currentArticle" class="table-view">
          <!-- 人物列表 -->
          <el-card class="analysis-card" v-if="currentAnalysis.characters.length > 0">
            <template #header>
              <div class="card-header">
                <span>人物列表</span>
                <span class="data-count">共 {{ currentAnalysis.characters.length }} 个人物</span>
              </div>
            </template>
            <el-table :data="currentAnalysis.characters" style="width: 100%">
              <el-table-column prop="name" label="姓名" width="120" />
              <el-table-column prop="description" label="描述" />
              <el-table-column prop="faction" label="势力" width="120" />
            </el-table>
          </el-card>

          <!-- 势力列表 -->
          <el-card class="analysis-card" v-if="currentAnalysis.factions && currentAnalysis.factions.length > 0">
            <template #header>
              <div class="card-header">
                <span>势力列表</span>
                <span class="data-count">共 {{ currentAnalysis.factions.length }} 个势力</span>
              </div>
            </template>
            <el-table :data="currentAnalysis.factions" style="width: 100%">
              <el-table-column prop="name" label="名称" width="120" />
              <el-table-column prop="description" label="描述" />
            </el-table>
          </el-card>

          <!-- 关系列表 -->
          <el-card class="analysis-card" v-if="currentAnalysis.relationships.length > 0">
            <template #header>
              <div class="card-header">
                <span>关系列表</span>
                <span class="data-count">共 {{ currentAnalysis.relationships.length }} 个关系</span>
              </div>
            </template>
            <el-table :data="currentAnalysis.relationships" style="width: 100%">
              <el-table-column prop="source" label="源节点" min-width="120">
                <template #default="scope">
                  {{ scope.row.source }}
                </template>
              </el-table-column>
              <el-table-column prop="target" label="目标节点" min-width="120">
                <template #default="scope">
                  {{ scope.row.target }}
                </template>
              </el-table-column>
              <el-table-column prop="type" label="关系类型" min-width="120">
                <template #default="scope">
                  {{ getRelationTypeChinese(scope.row.type) }}
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" min-width="200" />
            </el-table>
          </el-card>

          <!-- 事件列表 -->
          <el-card class="analysis-card" v-if="currentAnalysis.events && currentAnalysis.events.length > 0">
            <template #header>
              <div class="card-header">
                <span>事件列表</span>
                <span class="data-count">共 {{ currentAnalysis.events.length }} 个事件</span>
              </div>
            </template>
            <el-table :data="currentAnalysis.events" style="width: 100%">
              <el-table-column label="标题" prop="title" min-width="150" />
              <el-table-column label="描述" prop="description" min-width="200" />
              <el-table-column label="时间" prop="time" min-width="100" />
              <el-table-column label="地点" prop="location" min-width="100" />
              <el-table-column label="参与者" min-width="150">
                <template #default="scope">
                  {{ scope.row.participants.join(', ') }}
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </div>

        <div v-else-if="viewMode === 'graph'" class="graph-view">
          <div ref="graphRef" class="graph-container"></div>
    </div>

        <div v-else class="empty-state">
          <el-empty description="请选择一篇文章" />
          </div>
        </div>

      <div class="right-panel">
        <!-- 工具栏 -->
        <div class="toolbar">
          <el-button type="primary" @click="showUploadDialog = true">
            新建分析
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>

        <!-- 文章列表 -->
        <div class="article-list">
          <template v-if="articleList.length > 0">
            <!-- 按作品分组显示文章 -->
            <div v-for="work in groupedArticles" :key="work.work_id" class="work-group">
              <h1 class="work-title">{{ work.work_name }}</h1>
                <div 
                  v-for="article in work.articles" 
                  :key="article.id"
                  class="article-item"
                  :class="{ active: currentArticle?.id === article.id }"
                @click="handleArticleClick(article)"
                >
                <div class="article-info">
                  <h2 class="article-title">{{ article.title }}</h2>
                  <div class="article-meta">
                    <span class="time">{{ article.created_at }}</span>
                  </div>
                </div>
                <el-button 
                  type="danger" 
                  link
                  @click.stop="deleteArticle(article.id)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
                  </div>
                </div>
          </template>
          <el-empty v-else description="暂无文章" />
              </div>
          </div>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="新建分析"
      width="60%"
    >
      <el-input
        v-model="articleContent"
        type="textarea"
        :rows="10"
        placeholder="请输入文章内容..."
      />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showUploadDialog = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleAnalyze"
            :loading="analyzing"
          >
            开始分析
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight, Delete } from '@element-plus/icons-vue'
import axios from 'axios'
import * as echarts from 'echarts'
import KnowledgeGraph from './KnowledgeGraph.vue'

// 初始化分析数据结构
const initializeAnalysisData = () => ({
  characters: [],
  factions: [],
  relationships: [],
  events: []
})

// 状态定义
const loading = ref(false)
const analyzing = ref(false)
const articleList = ref([])
const expandedWorks = ref([])
const currentArticle = ref(null)
const currentAnalysis = ref(initializeAnalysisData())
const viewMode = ref('table')
const articleContent = ref('')
const showUploadDialog = ref(false)
const graphRef = ref(null)
let graphChart = null

// 调试状态
const debug = ref(true)

// 关系类型中英文映射
const relationTypeMap = {
  'monarch-minister': '君臣',
  'master-apprentice': '师徒',
  'friend': '朋友',
  'enemy': '敌人',
  'family': '家人',
  'spouse': '配偶',
  'belongs_to': '属于',
  'leads': '领导',
  'affiliated': '附属',
  'opposes': '对立',
  'ENEMY': '敌对',
  'FAMILY': '家人',
  'FRIEND': '朋友',
  'MASTER_APPRENTICE': '师徒',
  'MONARCH_MINISTER': '君臣'
}

// 转换关系类型为中文
const getRelationTypeChinese = (type) => {
  return relationTypeMap[type] || type
}

// 方法定义
const fetchArticleList = async () => {
  loading.value = true
  try {
    console.log('开始获取文章列表')
    const response = await axios.get('/api/article/list/')
    console.log('API响应:', response.data)
    
    if (response.data.code === 0) {
      // 处理文章列表数据，确保每篇文章都有正确的ID
      const works = response.data.data || []
      const articles = []
      
      // 展开作品中的文章列表
      works.forEach(work => {
        if (work.articles && Array.isArray(work.articles)) {
          work.articles.forEach(article => {
            articles.push({
              ...article,
              work_id: work.work_id,
              work_name: work.work_name
            })
          })
        }
      })
      
      articleList.value = articles
      console.log('处理后的文章列表:', articleList.value)
      
      // 如果有文章，加载第一篇
      if (articles.length > 0) {
        await loadArticle(articles[0])
      } else {
        console.log('暂无文章数据')
        resetView()
      }
    } else {
      console.error('获取列表失败:', response.data.message)
      ElMessage.error(response.data.message || '获取列表失败')
      resetView()
    }
  } catch (error) {
    console.error('获取文章列表失败:', error)
    ElMessage.error('获取列表失败：' + error.message)
    resetView()
  } finally {
    loading.value = false
  }
}

const analyzeArticle = async () => {
  if (!articleContent.value.trim()) {
    ElMessage.warning('请输入文章内容')
    return
  }

  analyzing.value = true
  try {
    const response = await axios.post('/api/article/analyze/', {
      content: articleContent.value
    })

    if (response.data.code === 0) {
      ElMessage.success('分析成功')
      showUploadDialog.value = false
      
      // 更新当前文章和分析结果
      const { article_id, analysis } = response.data.data
      
      // 加载新文章详情
      const articleResponse = await axios.get(`/api/article/${article_id}/`)
      if (articleResponse.data.code === 0) {
        currentArticle.value = articleResponse.data.data
        
        // 尝试加载分析结果
        try {
          const analysisResponse = await axios.get(`/api/article/${article_id}/analysis/`)
          console.log('分析结果响应:', analysisResponse)
          console.log('分析结果数据:', analysisResponse.data)
          
          if (analysisResponse.data.code === 0) {
            const analysisData = analysisResponse.data.data
            console.log('原始分析数据:', analysisData)
            
            // 处理分析数据
            const processedData = processAnalysisData(analysisData)
            
            // 更新分析数据
            currentAnalysis.value = {
              characters: processedData.characters,
              factions: processedData.forces,
              events: processedData.events,
              relationships: processedData.relationships
            }
            
            console.group('最终处理结果')
            console.log('节点数据:', {
              characters: currentAnalysis.value.characters,
              factions: currentAnalysis.value.factions
            })
            console.table(currentAnalysis.value.relationships)
            console.groupEnd()
            
            // 如果是图谱模式，更新图表
            if (viewMode.value === 'graph') {
              // 创建节点ID到索引的映射
              const nodeIdToIndex = new Map()
              processedData.nodes.forEach((node, index) => {
                nodeIdToIndex.set(node.id.toString(), index)
              })
              
              // 处理节点数据
              const graphNodes = processedData.nodes.map(node => {
                const nodeType = node.type.toLowerCase()
                const category = nodeType === 'character' ? 0 : 1
                
                return {
                  id: node.id,
                  name: node.name,
                  value: node.value,
                  category: category,
                  symbolSize: nodeType === 'character' ? 40 : 50,
                  itemStyle: {
                    color: nodeType === 'character' ? '#4B6BF5' : '#51cf66'
                  },
                  label: {
                    show: true,
                    position: 'right',
                    formatter: node.name
                  }
                }
              })
              
              // 处理关系数据
              const graphLinks = processedData.relationships.map(rel => {
                const sourceNode = processedData.nodes.find(n => n.name === rel.source)
                const targetNode = processedData.nodes.find(n => n.name === rel.target)
                
                if (!sourceNode || !targetNode) {
                  console.warn('找不到关系的源节点或目标节点:', rel)
                  return null
                }
                
                const sourceIndex = nodeIdToIndex.get(sourceNode.id.toString())
                const targetIndex = nodeIdToIndex.get(targetNode.id.toString())
                
                return {
                  source: sourceIndex,
                  target: targetIndex,
                  value: rel.value,
                  symbolSize: [5, 5],
                  lineStyle: {
                    color: getRelationColor(rel.value),
                    width: 2,
                    curveness: 0.2
                  },
                  label: {
                    show: true,
                    formatter: rel.value,
                    fontSize: 12
                  }
                }
              }).filter(link => link !== null)
              
              // 更新图表配置
              if (graphChart) {
                const option = {
                  title: {
                    text: '文章知识图谱',
                    top: 'top',
                    left: 'center'
                  },
                  tooltip: {
                    formatter: function(params) {
                      if (params.dataType === 'node') {
                        return `${params.data.name}<br/>${params.data.value || ''}`
                      } else {
                        return params.data.value || ''
                      }
                    }
                  },
                  legend: {
                    data: ['人物', '势力'],
                    top: 30
                  },
                  animationDurationUpdate: 1500,
                  animationEasingUpdate: 'quinticInOut',
                  series: [{
                    type: 'graph',
                    layout: 'force',
                    data: graphNodes,
                    links: graphLinks,
                    categories: [
                      { 
                        name: '人物',
                        itemStyle: {
                          color: '#4B6BF5'
                        }
                      },
                      { 
                        name: '势力',
                        itemStyle: {
                          color: '#51cf66'
                        }
                      }
                    ],
                    roam: true,
                    label: {
                      show: true,
                      position: 'right',
                      fontSize: 12
                    },
                    force: {
                      repulsion: 300,
                      edgeLength: 150,
                      gravity: 0.1,
                      layoutAnimation: true
                    },
                    emphasis: {
                      focus: 'adjacency',
                      lineStyle: {
                        width: 4
                      }
                    }
                  }]
                }
                
                console.log('设置图表配置')
                graphChart.setOption(option)
                console.log('图表配置已更新')
              }
            }
          } else {
            console.warn('获取分析结果失败:', analysisResponse.data.message)
            resetAnalysisData()
          }
        } catch (error) {
          console.error('加载分析结果失败:', error)
          resetAnalysisData()
        }
      }
      
      // 刷新文章列表
      await fetchArticleList()
    } else {
      ElMessage.error(response.data.message || '分析失败')
    }
  } catch (error) {
    console.error('分析文章失败:', error)
    ElMessage.error('分析失败：' + (error.response?.data?.message || error.message))
  } finally {
    analyzing.value = false
    articleContent.value = ''
  }
}

// 添加 handleAnalyze 函数
const handleAnalyze = async () => {
  if (!articleContent.value.trim()) {
    ElMessage.warning('请输入文章内容')
    return
  }
  await analyzeArticle()
}

const loadArticle = async (article) => {
  if (!article) {
    console.warn('未提供文章数据')
    return
  }
  
  currentArticle.value = article
  loading.value = true
  try {
    console.log('开始加载文章详情:', article.id)
    const response = await axios.get(`/api/article/${article.id}/`)
    console.log('文章详情响应:', response.data)
    
    if (response.data.code === 0) {
      const articleData = response.data.data
      // 更新当前文章的完整信息
      currentArticle.value = {
        ...article,
        content: articleData.content,
        work_name: articleData.work_name
      }
      
      // 尝试加载分析结果
      try {
        const analysisResponse = await axios.get(`/api/article/${article.id}/analysis/`)
        console.log('分析结果响应:', analysisResponse)
        console.log('分析结果数据:', analysisResponse.data)
        
        if (analysisResponse.data.code === 0) {
          const analysisData = analysisResponse.data.data
          console.log('原始分析数据:', analysisData)
          
          // 处理分析数据
          const processedData = processAnalysisData(analysisData)
          
          // 更新分析数据
          updateAnalysisData(processedData)
          
          // 如果是图谱模式，更新图表
          if (viewMode.value === 'graph') {
            await updateGraphData(processedData)
          }
        } else {
          console.warn('获取分析结果失败:', analysisResponse.data.message)
          resetAnalysisData()
        }
      } catch (error) {
        console.error('加载分析结果失败:', error)
        resetAnalysisData()
      }
    } else {
      console.error('加载文章详情失败:', response.data.message)
      ElMessage.error(response.data.message || '加载文章失败')
      resetView()
    }
  } catch (error) {
    console.error('加载文章详情失败:', error)
    ElMessage.error('加载文章失败：' + error.message)
    resetView()
  } finally {
    loading.value = false
  }
}

const resetAnalysisData = () => {
  currentAnalysis.value = {
    characters: [],
    factions: [],
    events: [],
    relationships: []
  }
}

const resetView = () => {
  currentArticle.value = null
  resetAnalysisData()
  articleContent.value = ''
  showUploadDialog.value = false
}

const toggleWork = (workId) => {
  const index = expandedWorks.value.indexOf(workId)
  if (index === -1) {
    expandedWorks.value.push(workId)
  } else {
    expandedWorks.value.splice(index, 1)
  }
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleString()
}

const closeUploadDialog = () => {
  showUploadDialog.value = false
}

const deleteArticle = async (articleId) => {
  try {
    // 添加确认对话框
    await ElMessageBox.confirm(
      '确定要删除这篇文章吗？删除后无法恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    const response = await axios.delete(`/api/article/${articleId}/delete/`)
    if (response.data.code === 0) {
      ElMessage.success('文章删除成功')
      // 如果当前显示的是被删除的文章，清空显示
      if (currentArticle.value?.id === articleId) {
        currentArticle.value = null
        currentAnalysis.value = initializeAnalysisData()
      }
      // 刷新文章列表
      await fetchArticleList()
    } else {
      // 如果返回的是文章不存在的错误，也刷新列表
      if (response.data.message.includes('未找到')) {
        await fetchArticleList()
      }
      ElMessage.error(response.data.message || '删除失败')
    }
  } catch (error) {
    if (error.name === 'CanceledError' || error.toString().includes('cancel')) {
      // 用户取消删除，不做任何处理
      return
    }
    
    console.error('删除文章失败:', error)
    // 如果是 404 错误，说明文章已经被删除
    if (error.response?.status === 404 || error.response?.data?.message?.includes('未找到')) {
      await fetchArticleList() // 刷新列表
      ElMessage.warning('文章已被删除')
    } else {
      ElMessage.error('删除失败：' + (error.response?.data?.message || error.message))
    }
  }
}

// 处理作品选择变化
const handleWorkChange = async (workId) => {
  console.log('选择作品:', workId)
  // 不再在这里调用 loadGraphData
}

// 处理文章点击
const handleArticleClick = async (article) => {
  if (!article || !article.id) {
    console.error('无效的文章数据:', article)
    return
  }

  try {
    // 先更新当前文章，这样标题就会立即显示
    currentArticle.value = article
    console.log('加载文章:', article)
    
    // 获取文章详情
    const detailResponse = await axios.get(`/api/article/${article.id}/`)
    if (detailResponse.data.code === 0) {
      // 合并新数据，保留原有数据
      currentArticle.value = {
        ...currentArticle.value,
        ...detailResponse.data.data
      }
      
      // 获取文章分析结果
      const analysisResponse = await axios.get(`/api/article/${article.id}/analysis/`)
      if (analysisResponse.data.code === 0) {
        const analysisData = analysisResponse.data.data
        console.log('获取到的分析数据:', analysisData)
        
        // 处理分析数据
        const processedData = processAnalysisData(analysisData)
        console.log('处理后的分析数据:', processedData)
        
        // 更新分析数据
        currentAnalysis.value = {
          characters: processedData.characters || [],
          factions: processedData.forces || [],
          events: processedData.events || [],
          relationships: processedData.relationships || []
        }
        
        console.log('更新后的分析数据:', currentAnalysis.value)
      }
      
      // 如果是图谱模式，获取并展示知识图谱数据
      if (viewMode.value === 'graph') {
        await loadGraphData(article.id)
      }
    } else {
      ElMessage.error(detailResponse.data.message || '获取文章详情失败')
    }
  } catch (error) {
    console.error('获取文章信息失败:', error)
    ElMessage.error('获取文章信息失败')
    // 如果是 404 错误，可能文章已被删除，刷新列表
    if (error.response?.status === 404) {
      await fetchArticleList()
    }
  }
}

// 监听视图模式变化
watch(viewMode, async (newMode) => {
  console.log('视图模式切换:', newMode)
  if (newMode === 'graph') {
    await nextTick()
    console.log('初始化图表')
    initChart()
    
    // 获取当前选中的文章ID
    const articleId = currentArticle.value?.id
    
    if (articleId) {
      console.log('加载图谱数据:', articleId)
      await loadGraphData(articleId)
    } else {
      console.warn('当前没有选中的文章')
    }
  }
})

// 初始化图表
const initChart = () => {
  console.log('开始初始化图表')
  if (graphChart) {
    console.log('销毁旧图表实例')
    graphChart.dispose()
  }
  
  if (graphRef.value) {
    console.log('创建新图表实例')
    graphChart = echarts.init(graphRef.value)
    const option = {
      title: {
        text: '文章知识图谱',
        top: 'top',
        left: 'center'
      },
      tooltip: {
        formatter: function(params) {
          if (params.dataType === 'node') {
            return `${params.data.name}<br/>${params.data.value || ''}`
          } else {
            return params.data.value || ''
          }
        }
      },
      legend: {
        data: ['人物', '势力'],
        top: 30
      },
      animationDurationUpdate: 1500,
      animationEasingUpdate: 'quinticInOut',
      series: [{
        type: 'graph',
        layout: 'force',
        data: [],
        links: [],
        categories: [
          { 
            name: '人物',
            itemStyle: {
              color: '#4B6BF5'
            }
          },
          { 
            name: '势力',
            itemStyle: {
              color: '#51cf66'
            }
          }
        ],
        roam: true,
        label: {
          show: true,
          position: 'right',
          fontSize: 14,
          color: '#333'
        },
        force: {
          repulsion: 500,
          edgeLength: 150,
          gravity: 0.1,
          layoutAnimation: true
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          }
        }
      }]
    }
    console.log('设置初始图表配置')
    graphChart.setOption(option)
  } else {
    console.warn('图表容器元素不存在')
  }
}

// 渲染知识图谱
const renderGraph = (data) => {
  if (!graphChart || !data) return
  
  console.log('原始图谱数据:', JSON.stringify(data, null, 2))
  
  // 创建节点ID到索引的映射
  const nodeIdMap = {}
  data.nodes.forEach((node, index) => {
    nodeIdMap[node.id] = index
    console.log(`映射节点 ID ${node.id} -> 索引 ${index}`)
  })
  
  // 处理节点数据
  const nodes = data.nodes.map((node, index) => {
    const category = getCategoryIndex(node.type.toLowerCase())
    console.log(`处理节点: ${node.name}, 类型: ${node.type}, 分类索引: ${category}`)
    return {
      id: node.id,
      name: node.name,
      value: node.description,
      category: category,
      symbolSize: node.type.toLowerCase() === 'force' ? 60 : 40,
      label: {
        show: true,
        position: 'right',
        formatter: node.name
      },
      tooltip: {
        formatter: `${node.name}<br/>${node.description || ''}`
      }
    }
  })

  console.log('处理后的节点数据:', nodes)

  // 处理边数据
  const edges = data.links.map(link => {
    const sourceIndex = nodeIdMap[link.source]
    const targetIndex = nodeIdMap[link.target]
    
    console.log(`处理关系: ${link.source} -> ${link.target}, 映射后: ${sourceIndex} -> ${targetIndex}, 类型: ${link.type}`)
    
    if (sourceIndex === undefined || targetIndex === undefined) {
      console.warn('找不到节点索引:', link)
      return null
    }
    
    return {
      source: sourceIndex,
      target: targetIndex,
      value: link.type,
      symbolSize: [5, 5],
      lineStyle: {
        color: getRelationColor(link.type),
        width: 2,
        curveness: 0.2
      },
      label: {
        show: true,
        formatter: link.type,
        fontSize: 12
      }
    }
  }).filter(edge => edge !== null)

  console.log('处理后的边数据:', edges)

  // 更新图表配置
  const option = {
    title: {
      text: '文章知识图谱',
      top: 'top',
      left: 'center'
    },
    tooltip: {
      formatter: function(params) {
        if (params.dataType === 'node') {
          return `${params.data.name}<br/>${params.data.value || ''}`
        } else {
          return params.data.value || ''
        }
      }
    },
    legend: {
      data: ['人物', '势力', '事件'],
      top: 30
    },
    animationDurationUpdate: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: edges,
      categories: [
        { 
          name: '人物',
          itemStyle: {
            color: '#4B6BF5'
          }
        },
        { 
          name: '势力',
          itemStyle: {
            color: '#51cf66'
          }
        },
        { 
          name: '事件',
          itemStyle: {
            color: '#ffd43b'
          }
        }
      ],
      roam: true,
      label: {
        show: true,
        position: 'right',
        fontSize: 12
      },
      force: {
        repulsion: 200,
        gravity: 0.1,
        edgeLength: 100,
        layoutAnimation: true
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      lineStyle: {
        color: '#aaa',
        curveness: 0.3,
        width: 1
      }
    }]
  }
  
  graphChart.setOption(option)
}

// 获取节点类型对应的分类索引
const getCategoryIndex = (type) => {
  const typeMap = {
    'character': 0,
    'force': 1,
    'faction': 1,
    'event': 2
  }
  const normalizedType = type.toLowerCase()
  console.log('节点类型映射:', normalizedType, '->', typeMap[normalizedType])
  return typeMap[normalizedType] || 0
}

// 获取关系类型对应的颜色
const getRelationColor = (type) => {
  const colorMap = {
    '兄弟': '#722ed1',
    '君臣': '#fa8c16',
    '朋友': '#52c41a',
    '敌对': '#f5222d',
    '主仆': '#fa8c16',
    '师徒': '#1890ff',
    '家人': '#eb2f96',
    '属于': '#faad14',
    'belongs_to': '#faad14'
  }
  return colorMap[type] || '#aaa'
}

// 加载图谱数据
const loadGraphData = async (articleId) => {
  if (!articleId) {
    console.error('未提供文章ID')
    ElMessage.warning('无法加载知识图谱：未找到文章信息')
    return
  }
  
  try {
    const graphResponse = await axios.get(`/api/article/${articleId}/analysis/`)
    console.log('获取到的图谱数据:', graphResponse.data)
    
    if (graphResponse.data.code === 0) {
      const analysisData = graphResponse.data.data
      console.log('原始分析数据:', analysisData)
      
      // 创建节点ID到索引的映射
      const nodeIdMap = new Map()
      
      // 处理节点数据
      const nodes = []
      
      // 处理人物节点
      ;(analysisData.characters || []).forEach((char, index) => {
        const node = {
          id: `character_${index}`,
          name: char.name,
          value: char.description,
          type: 'character',
          faction: char.faction,
          category: 0,
          symbolSize: 40,
          itemStyle: {
            color: '#4B6BF5'
          },
          label: {
            show: true,
            position: 'right',
            formatter: char.name
          }
        }
        nodes.push(node)
        nodeIdMap.set(char.name, node)
      })
      
      // 处理势力节点
      ;(analysisData.forces || []).forEach((force, index) => {
        const node = {
          id: `force_${index}`,
          name: force.name,
          value: force.description,
          type: 'force',
          category: 1,
          symbolSize: 50,
          itemStyle: {
            color: '#51cf66'
          },
          label: {
            show: true,
            position: 'right',
            formatter: force.name
          }
        }
        nodes.push(node)
        nodeIdMap.set(force.name, node)
      })
      
      // 处理关系数据
      const relationships = []
      
      // 处理人物之间的关系
      if (analysisData.relationships) {
        analysisData.relationships.forEach(rel => {
          const sourceNode = nodeIdMap.get(rel.source || rel.from)
          const targetNode = nodeIdMap.get(rel.target || rel.to)
          
          if (sourceNode && targetNode) {
            relationships.push({
              source: nodes.indexOf(sourceNode),
              target: nodes.indexOf(targetNode),
              value: getRelationTypeChinese(rel.type),
              lineStyle: {
                color: getRelationColor(rel.type),
                width: 2,
                curveness: 0.2
              },
              label: {
                show: true,
                formatter: getRelationTypeChinese(rel.type)
              }
            })
          }
        })
      }
      
      // 处理人物和势力的归属关系
      nodes.forEach(node => {
        if (node.type === 'character' && node.faction) {
          const forceNode = Array.from(nodeIdMap.values()).find(n => 
            n.type === 'force' && n.name === node.faction
          )
          if (forceNode) {
            relationships.push({
              source: nodes.indexOf(node),
              target: nodes.indexOf(forceNode),
              value: '属于',
              lineStyle: {
                color: getRelationColor('belongs_to'),
                width: 2,
                curveness: 0.2
              },
              label: {
                show: true,
                formatter: '属于'
              }
            })
          }
        }
      })
      
      // 更新图表配置
      if (graphChart) {
        const option = {
          title: {
            text: '文章知识图谱',
            top: 'top',
            left: 'center'
          },
          tooltip: {
            formatter: function(params) {
              if (params.dataType === 'node') {
                return `${params.data.name}<br/>${params.data.value || ''}`
              } else {
                return params.data.value || ''
              }
            }
          },
          legend: {
            data: ['人物', '势力'],
            top: 30
          },
          animationDurationUpdate: 1500,
          animationEasingUpdate: 'quinticInOut',
          series: [{
            type: 'graph',
            layout: 'force',
            data: nodes,
            links: relationships,
            categories: [
              { 
                name: '人物',
                itemStyle: {
                  color: '#4B6BF5'
                }
              },
              { 
                name: '势力',
                itemStyle: {
                  color: '#51cf66'
                }
              }
            ],
            roam: true,
            label: {
              show: true,
              position: 'right',
              fontSize: 12
            },
            force: {
              repulsion: 400,
              edgeLength: 200,
              gravity: 0.2,
              layoutAnimation: true
            },
            emphasis: {
              focus: 'adjacency',
              lineStyle: {
                width: 4
              }
            }
          }]
        }
        
        console.log('设置图表配置')
        graphChart.setOption(option)
      }
    }
  } catch (error) {
    console.error('获取知识图谱数据失败:', error)
    ElMessage.error('获取知识图谱数据失败')
  }
}

// 监听窗口大小变化
const handleResize = () => {
  if (graphChart) {
    graphChart.resize()
  }
}

onMounted(() => {
  console.log('组件已挂载，开始获取文章列表')
  fetchArticleList()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (graphChart) {
    graphChart.dispose()
  }
})

// 在 script setup 部分添加计算属性
const groupedArticles = computed(() => {
  const groups = {}
  articleList.value.forEach(article => {
    if (!groups[article.work_id]) {
      groups[article.work_id] = {
        work_id: article.work_id,
        work_name: article.work_name,
        articles: []
      }
    }
    groups[article.work_id].articles.push(article)
  })
  return Object.values(groups)
})

// 处理分析数据
const processAnalysisData = (analysisData) => {
  console.group('处理分析数据')
  console.log('原始分析数据:', analysisData)
  
  // 处理事件数据
  const events = []
  if (analysisData.events) {
    console.log('开始处理事件数据，原始事件数据:', analysisData.events)
    analysisData.events.forEach(event => {
      // 确保 participants 是数组
      let participants = []
      if (event.participants) {
        if (Array.isArray(event.participants)) {
          participants = event.participants
        } else if (typeof event.participants === 'string') {
          participants = event.participants.split(',').map(p => p.trim())
        }
      }
      
      // 处理地点信息
      const location = event.location || event.place || '-'
      
      const processedEvent = {
        title: event.title || event.name || '',
        description: event.description || '',
        participants: participants,
        time: event.time || '-',
        location: location
      }
      events.push(processedEvent)
    })
  }

  // 处理人物节点
  const characters = []
  if (analysisData.characters) {
    analysisData.characters.forEach(char => {
      characters.push({
        name: char.name,
        description: char.description,
        faction: char.faction
      })
    })
  }
  
  // 处理势力节点
  const forces = []
  if (analysisData.forces) {
    analysisData.forces.forEach(force => {
      forces.push({
        name: force.name,
        description: force.description
      })
    })
  }
  
  // 转换节点数据为图形所需格式
  const nodes = []
  
  // 添加人物节点
  characters.forEach((char, index) => {
    nodes.push({
      id: `character_${index}`,
      name: char.name,
      value: char.description,
      type: 'character',
      faction: char.faction,
      category: 0,
      symbolSize: 40,
      itemStyle: {
        color: '#4B6BF5'
      },
      label: {
        show: true,
        position: 'right',
        formatter: char.name
      }
    })
  })
  
  // 添加势力节点
  forces.forEach((force, index) => {
    nodes.push({
      id: `force_${index}`,
      name: force.name,
      value: force.description,
      type: 'force',
      category: 1,
      symbolSize: 50,
      itemStyle: {
        color: '#51cf66'
      },
      label: {
        show: true,
        position: 'right',
        formatter: force.name
      }
    })
  })
  
  // 创建节点ID映射
  const nodeMap = new Map()
  nodes.forEach(node => {
    nodeMap.set(node.name, node)
  })
  
  // 处理关系数据 - 只处理人物之间的关系，不包括势力归属关系
  const relationships = []
  if (analysisData.relationships) {
    analysisData.relationships.forEach(rel => {
      // 查找源节点和目标节点
      const sourceNode = nodes.find(n => 
        n.name === (rel.from || rel.source) || 
        n.id === (rel.from || rel.source)
      )
      const targetNode = nodes.find(n => 
        n.name === (rel.to || rel.target) || 
        n.id === (rel.to || rel.target)
      )
      
      // 只添加人物之间的关系，跳过与势力相关的关系
      if (sourceNode && targetNode && 
          sourceNode.type === 'character' && 
          targetNode.type === 'character') {
        relationships.push({
          source: sourceNode.name,
          target: targetNode.name,
          type: rel.type,
          value: getRelationTypeChinese(rel.type),
          description: rel.description
        })
      }
    })
  }
  
  const result = {
    nodes,
    relationships,
    events,
    characters,
    forces
  }
  
  console.log('最终处理结果:', {
    节点数: nodes.length,
    关系数: relationships.length,
    事件数: events.length,
    人物数: characters.length,
    势力数: forces.length
  })
  console.groupEnd()
  
  return result
}

// 更新表格数据
const updateTableData = () => {
  if (!currentArticle.value || !analysisResult.value) return
  
  // 更新人物表格数据
  characterTableData.value = analysisResult.value.characters.map(char => ({
    name: char.name,
    description: char.description,
    faction: char.faction || '-'
  }))
  
  // 更新关系表格数据
  relationshipTableData.value = analysisResult.value.relationships.map(rel => ({
    source: rel.source,
    target: rel.target,
    type: rel.type,
    description: rel.description
  }))
  
  // 更新事件表格数据
  eventTableData.value = analysisResult.value.events.map(event => ({
    title: event.title,
    description: event.description,
    participants: Array.isArray(event.participants) ? event.participants.join(', ') : event.participants,
    time: event.time || '-',
    location: event.location || '-'
  }))
}

// 更新当前分析数据
const updateAnalysisData = (processedData) => {
  console.group('更新分析数据')
  console.log('处理后的数据:', processedData)
  
  currentAnalysis.value = {
    characters: processedData.characters,
    factions: processedData.forces,
    events: processedData.events,
    relationships: processedData.relationships
  }
  
  console.log('更新后的 currentAnalysis:', {
    人物数: currentAnalysis.value.characters?.length || 0,
    势力数: currentAnalysis.value.factions?.length || 0,
    事件数: currentAnalysis.value.events?.length || 0,
    关系数: currentAnalysis.value.relationships?.length || 0
  })
  console.groupEnd()
}
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.nav-bar {
  height: 60px;
  background-color: #2c3e50;
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.nav-brand {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  margin-right: 48px;
}

.nav-menu {
  display: flex;
  gap: 32px;
}

.nav-item {
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  font-size: 16px;
  padding: 8px 0;
  transition: all 0.3s;
}

.nav-item:hover {
  color: #fff;
}

.nav-item.active {
  color: #fff;
  position: relative;
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background-color: #409EFF;
}

.main-content {
  display: flex;
  margin-top: 60px;
  height: calc(100vh - 60px);
  position: relative;
  justify-content: space-between;
  padding-right: 300px;
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  margin: 0;
  padding: 0;
  width: calc(100vw - 600px);
  overflow: hidden;
  background: #fff;
}

.right-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  background: #fff;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.1);
  position: fixed;
  right: 0;
  top: 60px;
  bottom: 0;
  z-index: 100;
}

.toolbar {
  padding: 12px;
  background: #fff;
  border-bottom: 1px solid #eee;
}

.toolbar .el-button {
  width: 100%;
}

.article-list {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.article-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: all 0.3s;
}

.article-item:hover {
  background: #f5f7fa;
}

.article-item.active {
  background: #ecf5ff;
  border-left: 4px solid #409EFF;
}

.article-info {
  flex: 1;
  min-width: 0;
  padding-right: 12px;
}

.article-title {
  font-size: 15px;
  margin-bottom: 6px;
  color: #303133;
  font-weight: 500;
  line-height: 1.4;
}

.article-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.work-name {
  color: #409EFF;
  font-weight: 500;
}

.time {
  color: #909399;
}

.empty-state {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fff;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
}

.graph-view {
  flex: 1;
  position: relative;
  height: 100%;
  margin: 0;
  padding: 0;
}

.graph-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.view-controls {
  position: fixed;
  top: 72px;
  left: 50%;
  transform: translateX(calc(-50% - 150px));
  z-index: 10;
  background: rgba(255, 255, 255, 0.9);
  padding: 8px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.analysis-card {
  margin: 0;
  width: 100%;
  box-sizing: border-box;
  border-radius: 0;
}

.analysis-card:last-child {
  margin-bottom: 0;
}

.el-card {
  margin: 0;
  border: none;
  border-radius: 0;
  box-shadow: none;
  border-bottom: 1px solid #eee;
}

:deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

:deep(.el-card__body) {
  padding: 0;
}

:deep(.el-table) {
  width: 100% !important;
  border: none;
}

:deep(.el-table::before) {
  display: none;
}

:deep(.el-table__header) {
  background: #f8f9fa;
}

:deep(.el-table__row) {
  background: #fff;
}

:deep(.el-table td), :deep(.el-table th) {
  padding: 8px 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
}

.data-count {
  font-size: 14px;
  color: #909399;
}

.work-group {
  margin-bottom: 24px;
}

.work-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  padding: 16px 20px 12px;
  background: #f8f9fa;
}

.table-view {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
  background: #fff;
}

.event-title {
  font-weight: 600;
  margin-bottom: 6px;
  color: #303133;
}

.event-description {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-top: 6px;
}

.participant-tag {
  margin: 4px;
}

.el-tag + .el-tag {
  margin-left: 6px;
}
</style> 