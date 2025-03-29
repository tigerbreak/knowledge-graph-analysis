<template>
  <div class="events-container">
    <h2>事件列表</h2>
    
    <!-- 作品选择下拉框 -->
    <div class="work-selector">
      <el-select 
        v-model="selectedWorkId" 
        placeholder="请选择作品" 
        @change="handleWorkChange"
        :loading="loading"
        clearable
      >
        <el-option
          v-for="work in works"
          :key="work.id"
          :label="work.name"
          :value="work.id"
        />
      </el-select>
      <div v-if="loading" style="color: #666; margin-top: 10px;">
        正在加载...
      </div>
      <div v-else-if="works.length === 0" style="color: #f56c6c; margin-top: 10px;">
        暂无作品数据
      </div>
      <div v-else style="color: #67c23a; margin-top: 10px;">
        共有 {{ works.length }} 个作品
      </div>
    </div>

    <!-- 事件列表 -->
    <div class="events-list">
      <el-table 
        :data="events" 
        style="width: 100%"
        v-loading="loading"
        :empty-text="loading ? '加载中...' : '暂无事件数据'"
      >
        <el-table-column prop="title" label="事件标题" min-width="180" />
        <el-table-column prop="time" label="发生时间" min-width="120" />
        <el-table-column prop="location" label="发生地点" min-width="120" />
        <el-table-column prop="description" label="事件描述" min-width="200" />
        <el-table-column label="参与者" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="participant in (Array.isArray(row.participants) ? row.participants : [])"
              :key="participant"
              class="participant-tag"
            >
              {{ participant }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import http from '../utils/http'

const works = ref([])
const events = ref([])
const selectedWorkId = ref('')
const loading = ref(false)

// 获取作品列表和事件列表
const fetchData = async (workId = null) => {
  loading.value = true
  try {
    console.log('开始获取事件数据')
    const url = workId ? `/events/${workId}/` : '/events/'
    const response = await http.get(url)
    console.log('获取到数据:', response.data)

    if (response.data.code === 0 && response.data.data) {
      works.value = response.data.data.works || []
      events.value = response.data.data.events || []
      console.log('作品列表:', works.value)
      console.log('事件列表:', events.value)
    } else {
      ElMessage.error(response.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// 处理作品选择变化
const handleWorkChange = (workId) => {
  console.log('选择作品:', workId)
  fetchData(workId)
}

// 页面加载时获取数据
onMounted(() => {
  console.log('Events组件已挂载')
  fetchData()
})
</script>

<style scoped>
.events-container {
  padding: 20px;
}

.work-selector {
  margin-bottom: 20px;
}

.participant-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.events-list {
  margin-top: 20px;
}

:deep(.el-select) {
  width: 200px;
}
</style> 