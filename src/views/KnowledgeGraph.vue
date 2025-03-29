<template>
  <div class="knowledge-graph-view">
    <el-card class="graph-card">
      <template #header>
        <div class="card-header">
          <h2>人物知识图谱</h2>
          <div class="controls">
            <el-select 
              v-model="selectedWork" 
              placeholder="选择作品" 
              @change="handleWorkChange"
              :loading="loading"
            >
              <el-option
                v-for="work in works"
                :key="work.id"
                :label="work.name"
                :value="work.id"
              />
            </el-select>
          </div>
        </div>
      </template>
      
      <div class="graph-container">
        <div v-if="loading" class="loading-overlay">
          <el-skeleton :rows="10" animated />
        </div>
        <div v-else-if="!graphData" class="empty-state">
          <el-empty description="请选择作品查看知识图谱" />
        </div>
        <div v-else ref="graphRef" class="graph-view"></div>
      </div>
    </el-card>

    <!-- 图谱信息面板 -->
    <el-drawer
      v-model="drawerVisible"
      :title="drawerTitle"
      direction="rtl"
      size="400px"
    >
      <div v-if="selectedNode" class="node-info">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ selectedNode.category === 0 ? '人物' : '势力' }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ selectedNode.value }}</el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedNode.category === 0" class="relationships">
          <h3>相关关系</h3>
          <el-table :data="nodeRelations" border stripe>
            <el-table-column prop="target" label="相关人物/势力" />
            <el-table-column prop="description" label="关系描述" />
          </el-table>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { graphService } from '../services/graphService'

// 状态定义
const graphRef = ref(null)
const loading = ref(false)
const selectedWork = ref('')
const works = ref([])
const graphData = ref(null)
const drawerVisible = ref(false)
const drawerTitle = ref('')
const selectedNode = ref(null)
const nodeRelations = ref([])
let graphInstance = null

// 获取作品列表
const fetchWorks = async () => {
  loading.value = true
  try {
    const response = await graphService.getWorks()
    if (response.code === 0) {
      works.value = response.data
    } else {
      ElMessage.error(response.message || '获取作品列表失败')
    }
  } catch (error) {
    ElMessage.error('获取作品列表失败')
  } finally {
    loading.value = false
  }
}

// 获取知识图谱数据
const fetchGraphData = async (workId) => {
  loading.value = true
  try {
    const response = await graphService.getGraphData(workId)
    if (response.code === 0) {
      graphData.value = response.data
      renderGraph(response.data)
    } else {
      ElMessage.error(response.message || '获取图谱数据失败')
    }
  } catch (error) {
    ElMessage.error('获取图谱数据失败')
  } finally {
    loading.value = false
  }
}

// 渲染图谱
const renderGraph = (data) => {
  if (!graphRef.value) return

  if (graphInstance) {
    graphInstance.dispose()
  }

  graphInstance = echarts.init(graphRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `${params.name}<br/>${params.value}`
        }
        return `${params.data.source} -> ${params.data.target}<br/>${params.data.value}`
      }
    },
    legend: {
      data: ['人物', '势力'],
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: data.nodes,
      links: data.links,
      categories: [
        { name: '人物' },
        { name: '势力' }
      ],
      roam: true,
      draggable: true,
      label: {
        show: true,
        position: 'right',
        formatter: '{b}'
      },
      force: {
        repulsion: 200,
        edgeLength: 120,
        gravity: 0.1
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      lineStyle: {
        color: '#409EFF',
        curveness: 0.3
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2
      }
    }]
  }

  graphInstance.setOption(option)

  // 点击节点显示详情
  graphInstance.on('click', async (params) => {
    if (params.dataType === 'node') {
      selectedNode.value = params.data
      drawerTitle.value = params.data.name
      
      try {
        const response = await graphService.getRelationships(params.data.id)
        if (response.code === 0) {
          nodeRelations.value = response.data
        }
      } catch (error) {
        console.error('获取关系详情失败:', error)
      }
      
      drawerVisible.value = true
    }
  })
}

// 处理作品选择变化
const handleWorkChange = (workId) => {
  if (workId) {
    fetchGraphData(workId)
  } else {
    graphData.value = null
    if (graphInstance) {
      graphInstance.dispose()
      graphInstance = null
    }
  }
}

// 生命周期钩子
onMounted(() => {
  fetchWorks()
  
  const handleResize = () => {
    graphInstance?.resize()
  }
  
  window.addEventListener('resize', handleResize)
  
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    if (graphInstance) {
      graphInstance.dispose()
    }
  })
})
</script>

<style scoped>
.knowledge-graph-view {
  height: calc(100vh - 100px);
  padding: 20px;
}

.graph-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.graph-card :deep(.el-card__body) {
  flex: 1;
  padding: 0;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.controls {
  display: flex;
  gap: 16px;
}

.graph-container {
  position: relative;
  height: 100%;
  background-color: #fff;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.graph-view {
  width: 100%;
  height: 100%;
}

.node-info {
  padding: 20px;
}

.relationships {
  margin-top: 20px;
}

.relationships h3 {
  margin-bottom: 16px;
  color: #303133;
  font-size: 16px;
}
</style> 