<template>
  <div class="factions-view">
    <el-card class="factions-card">
      <template #header>
        <div class="card-header">
          <h2>势力分布</h2>
          <div class="controls">
            <el-select v-model="selectedWork" placeholder="选择作品" @change="handleWorkChange">
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

      <!-- 势力关系图 -->
      <div class="graph-container">
        <div ref="graphRef" class="force-graph"></div>
      </div>

      <!-- 势力列表 -->
      <div class="factions-list">
        <el-collapse v-model="activeNames">
          <el-collapse-item
            v-for="faction in factions"
            :key="faction.id"
            :title="faction.name"
            :name="faction.id"
          >
            <template #title>
              <div class="faction-header">
                <span>{{ faction.name }}</span>
                <el-tag size="small" :type="getFactionTagType(faction)">
                  {{ faction.status }}
                </el-tag>
              </div>
            </template>

            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="势力描述">
                {{ faction.description }}
              </el-descriptions-item>
              <el-descriptions-item label="主要人物">
                <div class="character-tags">
                  <el-tag
                    v-for="character in faction.characters"
                    :key="character.name"
                    size="small"
                    effect="plain"
                    class="character-tag"
                  >
                    {{ character.name }}
                    <el-tooltip
                      :content="character.role"
                      placement="top"
                      effect="light"
                    >
                      <el-icon class="role-icon"><info-filled /></el-icon>
                    </el-tooltip>
                  </el-tag>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="影响力">
                <el-progress
                  :percentage="faction.influence"
                  :color="getInfluenceColor(faction.influence)"
                />
              </el-descriptions-item>
            </el-descriptions>

            <!-- 势力关系 -->
            <div class="faction-relationships">
              <h4>势力关系</h4>
              <el-table :data="faction.relationships" border size="small">
                <el-table-column prop="target" label="相关势力" />
                <el-table-column prop="type" label="关系类型">
                  <template #default="{ row }">
                    <el-tag :type="getRelationshipType(row.type)">
                      {{ row.type }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" show-overflow-tooltip />
              </el-table>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

export default {
  name: 'Factions',
  components: {
    InfoFilled
  },
  setup() {
    const selectedWork = ref('')
    const works = ref([])
    const factions = ref([])
    const activeNames = ref([])
    const graphRef = ref(null)
    let graphInstance = null

    // 获取作品列表
    const fetchWorks = async () => {
      try {
        const response = await fetch('/api/works/')
        const data = await response.json()
        if (data.code === 0) {
          works.value = data.data
        } else {
          ElMessage.error(data.message || '获取作品列表失败')
        }
      } catch (error) {
        ElMessage.error('获取作品列表失败')
      }
    }

    // 获取势力数据
    const fetchFactions = async (workId) => {
      try {
        const response = await fetch(`/api/factions/${workId}/`)
        const data = await response.json()
        if (data.code === 0) {
          factions.value = data.data
          renderGraph()
        } else {
          ElMessage.error(data.message || '获取势力数据失败')
        }
      } catch (error) {
        ElMessage.error('获取势力数据失败')
      }
    }

    // 渲染关系图
    const renderGraph = () => {
      if (!graphRef.value || !factions.value.length) return

      if (graphInstance) {
        graphInstance.dispose()
      }

      graphInstance = echarts.init(graphRef.value)

      // 准备节点和边的数据
      const nodes = factions.value.map(faction => ({
        name: faction.name,
        value: faction.influence,
        symbolSize: 30 + faction.influence / 2,
        category: faction.status
      }))

      const links = factions.value.reduce((acc, faction) => {
        const factionLinks = faction.relationships.map(rel => ({
          source: faction.name,
          target: rel.target,
          value: rel.type,
          lineStyle: {
            color: getRelationshipColor(rel.type)
          }
        }))
        return [...acc, ...factionLinks]
      }, [])

      const option = {
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            if (params.dataType === 'node') {
              const faction = factions.value.find(f => f.name === params.name)
              return `
                <div>
                  <h4>${faction.name}</h4>
                  <p>影响力: ${faction.influence}%</p>
                  <p>状态: ${faction.status}</p>
                </div>
              `
            }
            return `${params.data.source} -> ${params.data.target}<br/>${params.data.value}`
          }
        },
        legend: {
          data: ['活跃', '衰落', '灭亡'],
          orient: 'vertical',
          left: 'left',
          top: 'middle'
        },
        series: [{
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: links,
          categories: [
            { name: '活跃' },
            { name: '衰落' },
            { name: '灭亡' }
          ],
          roam: true,
          label: {
            show: true,
            position: 'right'
          },
          force: {
            repulsion: 200,
            edgeLength: 120
          },
          emphasis: {
            focus: 'adjacency'
          }
        }]
      }

      graphInstance.setOption(option)
    }

    // 处理作品选择变化
    const handleWorkChange = (workId) => {
      if (workId) {
        fetchFactions(workId)
      }
    }

    // 获取势力标签类型
    const getFactionTagType = (faction) => {
      const types = {
        '活跃': 'success',
        '衰落': 'warning',
        '灭亡': 'danger'
      }
      return types[faction.status] || 'info'
    }

    // 获取关系类型样式
    const getRelationshipType = (type) => {
      const types = {
        '盟友': 'success',
        '敌对': 'danger',
        '中立': 'info',
        '附属': 'warning'
      }
      return types[type] || ''
    }

    // 获取关系线条颜色
    const getRelationshipColor = (type) => {
      const colors = {
        '盟友': '#67C23A',
        '敌对': '#F56C6C',
        '中立': '#909399',
        '附属': '#E6A23C'
      }
      return colors[type] || '#909399'
    }

    // 获取影响力进度条颜色
    const getInfluenceColor = (influence) => {
      if (influence >= 80) return '#67C23A'
      if (influence >= 50) return '#E6A23C'
      return '#F56C6C'
    }

    onMounted(() => {
      fetchWorks()
      window.addEventListener('resize', () => {
        graphInstance?.resize()
      })
    })

    onUnmounted(() => {
      window.removeEventListener('resize', () => {
        graphInstance?.resize()
      })
      graphInstance?.dispose()
    })

    return {
      selectedWork,
      works,
      factions,
      activeNames,
      graphRef,
      handleWorkChange,
      getFactionTagType,
      getRelationshipType,
      getInfluenceColor
    }
  }
}
</script>

<style scoped>
.factions-view {
  padding: 20px;
}

.factions-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.controls {
  display: flex;
  gap: 16px;
}

.graph-container {
  height: 500px;
  margin-bottom: 20px;
}

.force-graph {
  width: 100%;
  height: 100%;
}

.faction-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.character-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.character-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.role-icon {
  font-size: 14px;
  cursor: help;
}

.faction-relationships {
  margin-top: 16px;
}

h4 {
  margin: 16px 0;
}
</style> 