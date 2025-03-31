<template>
  <div class="knowledge-graph-container">
    <div class="header">
      <h1>人物关系知识图谱</h1>
      <el-select v-model="selectedWork" placeholder="选择作品" clearable @change="handleWorkChange">
        <el-option
          v-for="work in works"
          :key="work.id"
          :label="work.name"
          :value="work.id"
        />
      </el-select>
    </div>
    
    <div ref="graphRef" class="graph-container"></div>
    
    <div class="legend">
      <div class="legend-item">
        <span class="dot character"></span>
        <span>人物</span>
      </div>
      <div class="legend-item">
        <span class="dot force"></span>
        <span>势力</span>
      </div>
      <div class="legend-item">
        <span class="line belongs"></span>
        <span>归属</span>
      </div>
      <div class="legend-item">
        <span class="line friend"></span>
        <span>友好</span>
      </div>
      <div class="legend-item">
        <span class="line enemy"></span>
        <span>敌对</span>
      </div>
      <div class="legend-item">
        <span class="line family"></span>
        <span>家族</span>
      </div>
      <div class="legend-item">
        <span class="line master"></span>
        <span>主仆</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'

const graphRef = ref(null)
const works = ref([])
const selectedWork = ref(null)
let graphChart = null

// 添加响应式变量存储当前分析数据
const currentAnalysis = ref({
  characters: [],
  factions: [],
  events: [],
  relationships: []
})

// 获取作品列表
const fetchWorks = async () => {
  try {
    const response = await axios.get('/api/works/')
    console.log('作品列表响应:', response.data)  // 添加日志
    if (response.data.code === 0) {
      works.value = response.data.data.map(work => ({
        id: work.id,
        name: work.name,
        articleCount: work.article_count
      }))
      console.log('处理后的作品列表:', works.value)  // 添加日志
    }
  } catch (error) {
    console.error('获取作品列表失败:', error)
    ElMessage.error('获取作品列表失败')
  }
}

// 初始化图表
const initChart = () => {
  if (graphChart) {
    graphChart.dispose()
  }
  
  if (graphRef.value) {
    console.log('初始化图表')
    graphChart = echarts.init(graphRef.value)
    const option = {
      title: {
        text: '人物关系知识图谱',
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
              color: '#4B6BF5'  // 蓝色
            }
          },
          { 
            name: '势力',
            itemStyle: {
              color: '#51cf66'  // 绿色
            }
          }
        ],
        roam: true,
        label: {
          show: true,
          position: 'right'
        },
        force: {
          repulsion: 300,
          edgeLength: [100, 200]
        },
        emphasis: {
          focus: 'adjacency'
        },
        lineStyle: {
          color: '#aaa',
          curveness: 0.3
        }
      }]
    }
    graphChart.setOption(option)
  }
}

// 获取节点类型对应的分类索引
const getCategoryIndex = (type) => {
  const typeMap = {
    'Character': 0,
    'Force': 1,
    'Faction': 1,
    'Event': 2,
    // 添加小写映射
    'character': 0,
    'force': 1,
    'faction': 1,
    'event': 2
  }
  console.log('节点类型映射:', type, '->', typeMap[type])
  return typeMap[type] || 0
}

// 获取关系颜色
const getRelationColor = (type) => {
  const colorMap = {
    '配偶': '#FF69B4',  // 粉红色
    '朋友': '#32CD32',  // 绿色
    '敌人': '#DC143C',  // 深红色
    '家人': '#FFD700',  // 金色
    '师徒': '#9370DB',  // 紫色
    '君臣': '#4169E1',  // 蓝色
    '归属': '#FFA500',  // 橙色
    '领导': '#8B4513',  // 棕色
    '附属': '#20B2AA',  // 青色
    '对立': '#FF4500'   // 红橙色
  }
  return colorMap[type] || '#666666'  // 默认灰色
}

// 加载图谱数据
const loadGraphData = async () => {
  try {
    loading.value = true
    console.log('开始加载图谱数据:', selectedWork.value)
    
    const response = await axios.get(`/api/work/${selectedWork.value}/graph/`)
    console.log('获取到的图谱数据:', response.data)
    
    if (response.data.code === 0) {
      const graphData = response.data.data
      
      // 创建节点ID到索引的映射
      const nodeIdToIndex = new Map()
      const nodes = []
      
      // 处理所有节点
      console.log('处理节点数据:', graphData.nodes?.length || 0)
      graphData.nodes.forEach((node, index) => {
        const processedNode = {
          id: index,
          name: node.name,
          value: node.description,
          type: node.type,
          faction: node.faction,
          category: getCategoryIndex(node.type),
          symbolSize: node.type === 'force' ? 50 : 40,
          itemStyle: {
            color: node.type === 'force' ? '#51cf66' : '#4B6BF5'
          },
          label: {
            show: true,
            position: 'right',
            formatter: node.name
          }
        }
        nodes.push(processedNode)
        nodeIdToIndex.set(node.name, index)
      })
      
      // 处理关系数据
      const links = []
      console.log('处理关系数据:', graphData.links?.length || 0)
      graphData.links.forEach(rel => {
        const sourceIndex = nodeIdToIndex.get(rel.source)
        const targetIndex = nodeIdToIndex.get(rel.target)
        
        if (sourceIndex !== undefined && targetIndex !== undefined) {
          links.push({
            source: sourceIndex,
            target: targetIndex,
            value: rel.chinese_type || rel.type,
            lineStyle: {
              color: getRelationColor(rel.chinese_type || rel.type),
              width: 2,
              curveness: 0.2
            },
            label: {
              show: true,
              formatter: rel.chinese_type || rel.type
            }
          })
          console.log(`创建关系: ${rel.source} -> ${rel.target} (${rel.chinese_type || rel.type})`)
        }
      })
      
      // 更新图表配置
      if (graphChart) {
        console.log('更新图表:', { nodes: nodes.length, links: links.length })
        const option = {
          tooltip: {
            show: true,
            formatter: (params) => {
              if (params.dataType === 'node') {
                return `${params.data.name}<br/>${params.data.value || ''}`
              } else {
                return `${params.data.value}`
              }
            }
          },
          legend: {
            data: ['人物', '势力']
          },
          series: [{
            type: 'graph',
            layout: 'force',
            data: nodes,
            links: links,
            categories: [
              { name: '人物' },
              { name: '势力' }
            ],
            roam: true,
            label: {
              show: true,
              position: 'right'
            },
            force: {
              repulsion: 100,
              gravity: 0.1,
              edgeLength: 100,
              layoutAnimation: true
            },
            lineStyle: {
              color: 'source',
              curveness: 0.2
            }
          }]
        }
        graphChart.setOption(option)
      }
    }
  } catch (error) {
    console.error('加载图谱数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 处理作品选择变化
const handleWorkChange = (workId) => {
  console.log('选择作品:', workId)
  selectedWork.value = workId
  loadGraphData(workId)
}

// 处理窗口大小变化
const handleResize = () => {
  if (graphChart) {
    graphChart.resize()
  }
}

// 更新图表配置
const updateChart = (data) => {
  if (!graphChart) return
  
  // 处理节点数据
  const processedNodes = data.nodes.map(node => ({
    id: node.id,
    name: node.name,
    value: node.description,
    type: node.type,
    category: getCategoryIndex(node.type),
    symbolSize: node.type === 'force' ? 50 : 40,
    itemStyle: {
      color: node.type === 'force' ? '#51cf66' : '#4B6BF5'
    },
    label: {
      show: true,
      position: 'right',
      formatter: node.name
    }
  }))
  
  // 处理关系数据
  const processedLinks = data.links.map(link => ({
    source: link.source,
    target: link.target,
    value: link.type,
    lineStyle: {
      color: getRelationColor(link.type),
      width: 2,
      curveness: 0.2
    },
    label: {
      show: true,
      formatter: link.type
    }
  }))
  
  const option = {
    title: {
      text: '人物关系图谱',
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
      data: processedNodes,
      links: processedLinks,
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
        edgeLength: [100, 200],
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
  
  console.group('图表配置')
  console.log('节点数据:', processedNodes)
  console.log('关系数据:', processedLinks)
  console.groupEnd()
  
  graphChart.setOption(option)
}

onMounted(async () => {
  console.log('组件已挂载')
  await fetchWorks()
  console.log('作品列表已获取')
  initChart()
  console.log('图表已初始化')
  await loadGraphData()  // 初始加载所有作品的图谱
  console.log('初始数据已加载')
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (graphChart) {
    graphChart.dispose()
  }
})
</script>

<style scoped>
.knowledge-graph-container {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.graph-container {
  flex: 1;
  min-height: 600px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 20px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.dot.character {
  background-color: #4B6BF5;  /* 蓝色 */
}

.dot.force {
  background-color: #51cf66;  /* 绿色 */
}

.line {
  width: 20px;
  height: 2px;
}

.line.belongs {
  background-color: #1890ff;
}

.line.friend {
  background-color: #52c41a;
}

.line.enemy {
  background-color: #f5222d;
}

.line.family {
  background-color: #722ed1;
}

.line.master {
  background-color: #eb2f96;
}
</style> 