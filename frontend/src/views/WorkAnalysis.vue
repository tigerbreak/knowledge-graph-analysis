<template>
  <div class="work-analysis">
    <div class="panel-container">
      <!-- 左侧面板 - 20% -->
      <div class="left-panel">
        <div class="header">
          <h2 class="title">作品列表</h2>
          <el-select
            v-model="selectedWork"
            placeholder="选择作品"
            class="work-select"
            @change="handleWorkChange"
          >
            <el-option
              v-for="work in workList"
              :key="work.id"
              :label="work.display_name || work.work_name"
              :value="work.id"
            />
          </el-select>
        </div>

        <!-- 图例说明 -->
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
            <span class="line friend"></span>
            <span>友好</span>
          </div>
          <div class="legend-item">
            <span class="line enemy"></span>
            <span>敌对</span>
          </div>
          <div class="legend-item">
            <span class="line belong"></span>
            <span>归属</span>
          </div>
          <div class="legend-item">
            <span class="line family"></span>
            <span>家族</span>
          </div>
        </div>
      </div>

      <!-- 右侧面板 - 80% -->
      <div class="right-panel">
        <div class="graph-title">人物关系知识图谱</div>
        <div class="graph-view">
          <div ref="graphRef" class="graph-container"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import * as echarts from 'echarts'

// 状态定义
const loading = ref(false)
const selectedWork = ref('')
const workList = ref([])
const graphRef = ref(null)
let graphChart = null

// 关系类型映射
const relationTypeMap = {
  'monarch-minister': '君臣',
  'master-apprentice': '师徒',
  'friend': '朋友',
  'enemy': '敌人',
  'family': '家族',
  'spouse': '配偶',
  'belongs_to': '归属',
  'leads': '领导',
  'affiliated': '附属',
  'opposes': '对立'
}

// 获取关系类型的中文名称
const getRelationTypeChinese = (type) => {
  return relationTypeMap[type] || type
}

// 获取关系颜色
const getRelationColor = (type) => {
  const colorMap = {
    'friend': '#52c41a',
    'enemy': '#f5222d',
    'family': '#722ed1',
    'belongs_to': '#faad14',
    'master-apprentice': '#1890ff',
    'monarch-minister': '#fa8c16'
  }
  return colorMap[type] || '#aaa'
}

// 初始化图表
const initChart = () => {
  if (graphChart) {
    graphChart.dispose()
  }
  
  if (graphRef.value) {
    graphChart = echarts.init(graphRef.value)
    const option = {
      title: {
        text: '作品人物关系图谱',
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
          fontSize: 14
        },
        force: {
          repulsion: 500,
          edgeLength: 200,
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
    graphChart.setOption(option)
  }
}

// 获取作品列表
const fetchWorkList = async () => {
  try {
    const response = await axios.get('/api/works/')
    console.log('作品列表响应:', response.data)  // 添加调试日志
    
    if (response.data.code === 0) {
      workList.value = response.data.data
      console.log('获取到的作品列表:', workList.value)  // 添加调试日志
      
      // 如果有作品数据，自动选择第一个
      if (workList.value.length > 0) {
        selectedWork.value = workList.value[0].id
        console.log('自动选择第一个作品:', selectedWork.value)  // 添加调试日志
        await loadWorkGraph(selectedWork.value)
      } else {
        console.log('没有可用的作品')  // 添加调试日志
      }
    } else {
      console.error('获取作品列表失败:', response.data.message)  // 添加调试日志
    }
  } catch (error) {
    console.error('获取作品列表失败:', error)
    ElMessage.error('获取作品列表失败')
  }
}

// 处理作品选择变化
const handleWorkChange = async (workId) => {
  console.log('选择作品:', workId)  // 添加调试日志
  if (workId) {
    await loadWorkGraph(workId)
  }
}

// 加载作品的知识图谱数据
const loadWorkGraph = async (workId) => {
  if (!workId) {
    console.error('未提供作品ID')
    return
  }
  
  console.log('开始加载作品图谱:', workId)
  loading.value = true
  
  try {
    const response = await axios.get(`/api/work/${workId}/graph/`)
    console.log('图谱数据响应:', response.data)
    
    if (response.data.code === 0) {
      const graphData = response.data.data
      console.log('获取到的图谱数据:', graphData)
      
      // 创建节点数据
      const nodes = []
      const nodeMap = new Map()
      
      // 处理所有节点
      if (graphData.nodes && Array.isArray(graphData.nodes)) {
        // 先去重节点
        const uniqueNodes = new Map()
        graphData.nodes.forEach(node => {
          if (!uniqueNodes.has(node.id)) {
            uniqueNodes.set(node.id, node)
          }
        })
        
        // 处理去重后的节点
        uniqueNodes.forEach((node) => {
          const processedNode = {
            id: node.id,
            name: node.name,
            value: node.description,
            category: node.category,
            symbolSize: 40,
            itemStyle: {
              color: node.category === 0 ? '#4B6BF5' : '#51cf66'
            },
            label: {
              show: true,
              formatter: node.name
            }
          }
          nodes.push(processedNode)
          nodeMap.set(node.id, processedNode)
        })
      }
      
      console.log('处理后的节点:', nodes)
      
      // 处理关系数据
      const links = []
      if (graphData.links && Array.isArray(graphData.links)) {
        graphData.links.forEach(link => {
          if (nodeMap.has(link.source) && nodeMap.has(link.target)) {
            links.push({
              source: link.source,
              target: link.target,
              value: link.chinese_type,
              symbolSize: 10,
              lineStyle: {
                color: getRelationColor(link.type),
                width: 2
              },
              label: {
                show: true,
                formatter: link.chinese_type
              }
            })
          }
        })
      }
      
      console.log('处理后的关系:', links)
      
      // 更新图表
      if (graphChart) {
        const option = {
          tooltip: {
            formatter: function(params) {
              if (params.dataType === 'node') {
                const node = nodeMap.get(params.data.id)
                return `${node.name}<br/>${node.value || ''}`
              } else {
                return params.data.value || ''
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
              position: 'right',
              formatter: '{b}'
            },
            force: {
              repulsion: 500,
              edgeLength: 200,
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
        graphChart.setOption(option)
        console.log('图表更新完成')
      }
    } else {
      console.error('获取图谱数据失败:', response.data.message)
      ElMessage.error('获取图谱数据失败')
    }
  } catch (error) {
    console.error('加载图谱失败:', error)
    ElMessage.error('加载图谱失败')
  } finally {
    loading.value = false
  }
}

// 监听窗口大小变化
const handleResize = () => {
  if (graphChart) {
    graphChart.resize()
  }
}

onMounted(() => {
  nextTick(() => {
    initChart()
    fetchWorkList() // 加载作品列表
  })
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
.work-analysis {
  width: 100%;
  flex: 1;                /* 继承父元素高度 */
  display: flex;          /* 使用 flex 布局 */
  flex-direction: column; /* 垂直方向排列 */
  min-height: 0;         /* 防止溢出 */
  background: #fff;
}

.panel-container {
  display: flex;
  flex: 1;              /* 占满剩余空间 */
  gap: 20px;
  padding: 20px;
  min-height: 0;        /* 防止溢出 */
}

.left-panel {
  width: 20%;
  /* min-width: 250px; */
  background: #fff;
  border-right: 1px solid #eee;
  display: flex;
  flex-direction: column;
  padding: 20px;
  min-height: 0;        /* 防止溢出 */
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  min-height: 0;        /* 防止溢出 */
}

.header {
  margin-bottom: 20px;
}

.title {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.work-select {
  width: 100%;
}

.graph-title {
  padding: 20px;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  border-bottom: 1px solid #eee;
}

.graph-view {
  flex: 1;
  position: relative;
}

.graph-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.legend {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.dot.character {
  background: #4B6BF5;
}

.dot.force {
  background: #51cf66;
}

.line {
  width: 20px;
  height: 2px;
}

.line.friend {
  background: #52c41a;
}

.line.enemy {
  background: #f5222d;
}

.line.belong {
  background: #faad14;
}

.line.family {
  background: #722ed1;
}
</style> 