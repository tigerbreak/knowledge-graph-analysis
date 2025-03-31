<script>
import http from '../utils/http'

export default {
  name: 'EventList',
  data() {
    return {
      events: [],
      works: [],
      selectedWork: null,
      loading: false
    }
  },
  created() {
    console.log('EventList组件已创建')
    this.fetchEvents()
  },
  methods: {
    async fetchEvents(workId = null) {
      this.loading = true
      try {
        const url = workId ? `/events/${workId}/` : '/events/'
        console.log('开始获取事件列表:', url)
        
        const response = await http.get(url)
        console.log('获取事件列表成功:', response.data)
        
        if (response.data.code === 0 && response.data.data) {
          this.events = response.data.data.events || []
          this.works = response.data.data.works || []
          
          console.log('作品列表:', this.works)
          console.log('事件列表:', this.events)
        }
      } catch (error) {
        console.error('获取事件列表失败:', error.message)
      } finally {
        this.loading = false
      }
    },
    handleWorkChange(value) {
      console.log('选择作品:', value)
      this.fetchEvents(value)
    }
  }
}
</script>

<template>
  <div class="event-list">
    <div class="work-selector">
      <el-select 
        v-model="selectedWork" 
        placeholder="请选择作品" 
        @change="handleWorkChange" 
        clearable
        :loading="loading"
      >
        <el-option
          v-for="work in works"
          :key="work.id"
          :label="work.name"
          :value="work.id"
        />
      </el-select>
      <div v-if="loading" style="color: #666; margin-top: 10px;">
        正在加载作品列表...
      </div>
      <div v-else-if="works.length === 0" style="color: #f56c6c; margin-top: 10px;">
        暂无作品数据
      </div>
      <div v-else style="color: #67c23a; margin-top: 10px;">
        共有 {{ works.length }} 个作品
      </div>
    </div>
    
    <el-table 
      :data="events" 
      v-loading="loading" 
      style="width: 100%; margin-top: 20px;"
      :empty-text="loading ? '加载中...' : '暂无事件数据'"
    >
      <el-table-column prop="title" label="事件名称" min-width="150"/>
      <el-table-column prop="description" label="描述" min-width="200"/>
      <el-table-column prop="location" label="地点" min-width="100"/>
      <el-table-column prop="time" label="时间" min-width="100"/>
      <el-table-column prop="participants" label="参与者" min-width="150">
        <template #default="{ row }">
          {{ Array.isArray(row.participants) ? row.participants.join('、') : row.participants }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<style scoped>
.event-list {
  padding: 20px;
}

.work-selector {
  margin-bottom: 20px;
}

:deep(.el-select) {
  width: 200px;
}
</style> 