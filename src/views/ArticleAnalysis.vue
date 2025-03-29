<template>
  <div class="container">
    <div class="main-content">
      <!-- 左侧面板 - 20% -->
      <div class="left-panel">
        <!-- 作品-文章导航树 -->
        <div class="nav-tree">
          <div class="tree-header">
            <h3>作品列表</h3>
            <div class="tree-actions">
              <el-button 
                type="primary" 
                @click="showAnalysisDialog"
                size="small"
              >
                新建分析
              </el-button>
            </div>
          </div>
          <el-tree
            ref="workTree"
            :data="workTreeData"
            :props="defaultProps"
            @node-click="handleNodeClick"
            node-key="id"
            :expand-on-click-node="false"
            highlight-current
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node">
                <span>{{ node.label }}</span>
                <div class="node-actions" v-if="data.created_at">
                  <span class="node-date">{{ formatDate(data.created_at) }}</span>
                  <el-button 
                    type="danger" 
                    link
                    size="small"
                    @click.stop="handleDelete(data)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>

      <!-- 右侧面板 - 80% -->
      <div class="right-panel">
        <div class="panel-header">
          <h2 class="panel-title">分析结果</h2>
          <div class="view-options">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="table">表格模式</el-radio-button>
              <el-radio-button label="graph">知识图谱</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <div class="panel-content" v-loading="loading">
          <template v-if="analysisResult">
            <!-- 知识图谱视图 -->
            <div v-show="viewMode === 'graph'" class="graph-container">
              <div ref="graphRef" class="graph-content"></div>
            </div>
            
            <!-- 表格视图 -->
            <div v-show="viewMode === 'table'" class="table-container">
              <!-- 人物列表 -->
              <div class="table-section">
                <div class="section-header">
                  <h3>人物列表</h3>
                </div>
                <el-table :data="analysisResult.characters" style="width: 100%">
                  <el-table-column prop="name" label="人物" width="120" />
                  <el-table-column prop="description" label="描述" />
                  <el-table-column prop="faction" label="势力" width="120" />
                </el-table>
              </div>
              
              <!-- 势力列表 -->
              <div class="table-section">
                <div class="section-header">
                  <h3>势力列表</h3>
                </div>
                <el-table :data="analysisResult.forces" style="width: 100%">
                  <el-table-column prop="name" label="势力" width="120" />
                  <el-table-column prop="description" label="描述" />
                </el-table>
              </div>
              
              <!-- 关系列表 -->
              <div class="table-section">
                <div class="section-header">
                  <h3>关系列表</h3>
                </div>
                <el-table :data="analysisResult.relationships" style="width: 100%">
                  <el-table-column prop="source" label="源节点" width="120" />
                  <el-table-column prop="target" label="目标节点" width="120" />
                  <el-table-column prop="type" label="关系类型" width="120" />
                  <el-table-column prop="description" label="描述" />
                </el-table>
              </div>

              <!-- 事件列表 -->
              <div class="table-section">
                <div class="section-header">
                  <h3>事件列表</h3>
                </div>
                <el-table :data="analysisResult.events" style="width: 100%">
                  <el-table-column prop="title" label="事件" width="120" />
                  <el-table-column prop="description" label="描述" />
                  <el-table-column prop="location" label="地点" width="120" />
                  <el-table-column prop="time" label="时间" width="120" />
                </el-table>
              </div>
            </div>
          </template>
          <div v-else class="empty-result">
            <el-empty description="暂无分析结果" />
          </div>
        </div>
      </div>
    </div>

    <!-- 新建分析弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建分析"
      width="50%"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-form :model="form">
        <el-form-item>
          <div class="upload-area">
            <el-upload
              class="upload-component"
              action="/api/article/upload/"
              :before-upload="beforeUpload"
              :on-success="handleUploadSuccess"
              :on-error="handleUploadError"
              :show-file-list="false"
              accept=".txt,.pdf,.docx"
            >
              <el-button type="primary">
                <el-icon><upload-filled /></el-icon>
                上传文件
              </el-button>
              <div class="upload-tip">支持 TXT、PDF、DOCX 格式文件</div>
            </el-upload>
          </div>
          <div class="divider">
            <span class="divider-text">或</span>
          </div>
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="12"
            placeholder="请输入或粘贴要分析的文本内容"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAnalyze" :loading="loading">
            开始分析
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

export default {
  name: 'ArticleAnalysis',
  components: {
    UploadFilled
  },
  setup() {
    const analysisResult = ref(null)
    const graphRef = ref(null)
    let graphInstance = null
    const dialogVisible = ref(false)
    const form = ref({
      content: ''
    })
    const loading = ref(false)
    const viewMode = ref('table')
    const workTreeData = ref([])
    const defaultProps = {
      children: 'articles',
      label: node => {
        // 如果是作品节点，显示作品名称
        if ('work_name' in node) {
          return node.work_name
        }
        // 如果是文章节点，显示文章标题
        return node.title
      }
    }
    const router = useRouter()

    // 获取作品和文章列表
    const fetchWorkList = async () => {
      try {
        const response = await fetch('/api/article/list/')
        const data = await response.json()
        if (data.code === 0) {
          workTreeData.value = data.data
        } else {
          ElMessage.error(data.message || '获取作品列表失败')
        }
      } catch (error) {
        ElMessage.error('获取作品列表失败')
      }
    }

    // 处理删除文章
    const handleDelete = async (article) => {
      try {
        const result = await ElMessageBox.confirm(
          '确定要删除这篇文章吗？',
          '提示',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        if (result === 'confirm') {
          const response = await fetch(`/api/article/${article.id}/delete/`, {
            method: 'DELETE'
          })
          const data = await response.json()
          
          if (data.code === 0) {
            ElMessage.success('删除成功')
            // 刷新作品列表
            fetchWorkList()
            // 如果当前显示的是被删除的文章，清空结果
            if (analysisResult.value && article.id === currentArticleId.value) {
              analysisResult.value = null
              currentArticleId.value = null
            }
          } else {
            ElMessage.error(data.message || '删除失败')
          }
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    // 添加 currentArticleId 用于跟踪当前显示的文章
    const currentArticleId = ref(null)

    // 修改 handleNodeClick，记录当前文章ID
    const handleNodeClick = async (data, node) => {
      // 如果点击的是文章节点
      if (data.created_at) {
        loading.value = true
        try {
          const response = await fetch(`/api/article/${data.id}/analysis/`)
          const result = await response.json()
          if (result.code === 0) {
            analysisResult.value = result.data
            currentArticleId.value = data.id  // 记录当前文章ID
            if (viewMode.value === 'graph') {
              nextTick(() => {
                renderGraph()
              })
            }
          } else {
            ElMessage.error(result.message || '获取分析结果失败')
          }
        } catch (error) {
          ElMessage.error('获取分析结果失败')
        } finally {
          loading.value = false
        }
      }
    }

    // 显示分析弹窗
    const showAnalysisDialog = () => {
      form.value.content = ''
      dialogVisible.value = true
    }

    // 处理上传成功
    const handleUploadSuccess = async (response) => {
      if (response.code === 0) {
        ElMessage.success('文件上传成功')
        // 将上传的内容填充到文本框
        form.value.content = response.data.content
      } else {
        ElMessage.error(response.message || '文件上传失败')
      }
    }

    // 处理上传失败
    const handleUploadError = () => {
      ElMessage.error('文件上传失败')
    }

    // 开始分析
    const handleAnalyze = async () => {
      if (!form.value.content.trim()) {
        ElMessage.warning('请输入或上传要分析的内容')
        return
      }

      dialogVisible.value = false
      loading.value = true

      // 从localStorage获取分片大小设置
      const chunkSize = parseInt(localStorage.getItem('chunkSize')) || 5000
      const content = form.value.content.trim()
      const segments = []
      for (let i = 0; i < content.length; i += chunkSize) {
        segments.push(content.slice(i, i + chunkSize))
      }

      // 显示总段数
      if (segments.length > 1) {
        ElMessage.info(`文本将分${segments.length}段进行分析，每段将生成独立的分析结果`)
      }
      
      try {
        // 逐段处理
        for (let i = 0; i < segments.length; i++) {
          // 显示当前处理进度
          if (segments.length > 1) {
            ElMessage.info(`正在分析第 ${i + 1}/${segments.length} 段文本`)
          }

          const result = await fetch('/api/article/analyze/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              content: segments[i]
            })
          })
          
          const data = await result.json()
          if (data.code === 0) {
            if (segments.length > 1) {
              ElMessage.success(`第 ${i + 1} 段分析完成`)
            } else {
              ElMessage.success('分析成功')
            }
            
            // 重新加载文章列表
            await fetchWorkList()

            // 如果还有下一段，等待一段时间再继续
            if (i < segments.length - 1) {
              await new Promise(resolve => setTimeout(resolve, 1000))
            }
          } else {
            ElMessage.error(data.message || '分析失败')
            break
          }
        }
      } catch (error) {
        console.error('分析失败:', error)
        ElMessage.error('分析请求失败')
      } finally {
        loading.value = false
      }
    }

    // 渲染知识图谱
    const renderGraph = () => {
      if (!graphRef.value) return
      
      if (!graphInstance) {
        graphInstance = echarts.init(graphRef.value)
      }

      const nodes = []
      const links = []

      // 添加人物节点
      analysisResult.value.characters.forEach(char => {
        nodes.push({
          name: char.name,
          value: char.description,
          category: 0,
          symbolSize: 50
        })
      })

      // 添加势力节点
      analysisResult.value.forces.forEach(force => {
        nodes.push({
          name: force.name,
          value: force.description,
          category: 1,
          symbolSize: 70
        })
      })

      // 添加关系边
      analysisResult.value.relationships.forEach(rel => {
        links.push({
          source: rel.source,
          target: rel.target,
          name: rel.type,
          value: rel.description
        })
      })

      const option = {
        title: {
          text: '知识图谱',
          top: 'bottom',
          left: 'right'
        },
        tooltip: {
          trigger: 'item',
          formatter: params => {
            if (params.dataType === 'node') {
              return `${params.name}<br/>${params.value || ''}`
            }
            return `${params.name}<br/>${params.value || ''}`
          }
        },
        legend: [{
          data: ['人物', '势力']
        }],
        animationDuration: 1500,
        animationEasingUpdate: 'quinticInOut',
        series: [{
          name: '知识图谱',
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
            repulsion: 1000,
            edgeLength: 200
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 10
            }
          }
        }]
      }

      graphInstance.setOption(option)
    }

    // 格式化日期
    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    }

    // 监听视图模式变化
    watch(viewMode, (newMode) => {
      if (newMode === 'graph' && analysisResult.value) {
        nextTick(() => {
          renderGraph()
        })
      }
    })

    // 上传前验证
    const beforeUpload = (file) => {
      const validTypes = {
        'text/plain': true,
        'application/pdf': true,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': true
      }
      
      if (!validTypes[file.type]) {
        ElMessage.error('只支持 TXT、PDF、DOCX 格式文件')
        return false
      }
      
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        ElMessage.error('文件大小不能超过 10MB')
        return false
      }
      
      return true
    }

    onMounted(() => {
      fetchWorkList()
      window.addEventListener('resize', () => {
        graphInstance?.resize()
      })
    })

    return {
      analysisResult,
      graphRef,
      form,
      loading,
      viewMode,
      workTreeData,
      defaultProps,
      handleNodeClick,
      formatDate,
      dialogVisible,
      showAnalysisDialog,
      handleAnalyze,
      handleDelete,
      currentArticleId,
      beforeUpload,
      handleUploadSuccess,
      handleUploadError
    }
  }
}
</script>

<style scoped>
.container {
  width: 100%;
  min-height: calc(100vh - 64px);
  padding: 20px;
  box-sizing: border-box;
  background: #f5f7fa;
}

.main-content {
  display: flex;
  gap: 20px;
  height: 100%;
}

.left-panel {
  width: 25%;
  min-width: 450px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.right-panel {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.panel-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.nav-tree {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tree-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.tree-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
  width: 100%;
}

.node-date {
  font-size: 12px;
  color: #909399;
  margin-right: 8px;
}

.node-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.3s;
}

.graph-container {
  height: calc(100vh - 180px);
  position: relative;
}

.graph-content {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.table-container {
  height: 100%;
  overflow-y: auto;
}

.table-section {
  margin-bottom: 24px;
}

.section-header {
  margin-bottom: 12px;
}

.section-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #606266;
}

.empty-result {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.view-options {
  display: flex;
  gap: 8px;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-textarea__inner) {
  font-family: system-ui, -apple-system, sans-serif;
  line-height: 1.6;
}

:deep(.el-tree-node__content:hover .node-actions) {
  opacity: 1;
}

:deep(.el-tree-node__content) {
  padding-right: 8px;
}

:deep(.el-button--danger.el-button--link) {
  font-size: 12px;
  height: 20px;
  line-height: 20px;
  padding: 0 4px;
  white-space: nowrap;
}

.upload-area {
  margin-bottom: 20px;
  text-align: center;
  padding: 20px;
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #409eff;
}

.upload-component {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

.divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: #909399;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #dcdfe6;
}

.divider-text {
  padding: 0 12px;
  font-size: 12px;
  color: #909399;
}
</style> 