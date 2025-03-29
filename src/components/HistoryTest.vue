<script>
export default {
  name: 'HistoryTest',
  data() {
    return {
      data: null,
      error: null
    }
  },
  created() {
    console.log('HistoryTest 组件已创建')
  },
  mounted() {
    console.log('HistoryTest 组件已挂载')
  },
  methods: {
    async testFetch() {
      console.log('开始测试获取数据')
      try {
        const response = await fetch('/api/article/list/')
        const data = await response.json()
        console.log('获取到数据:', data)
        this.data = data
      } catch (error) {
        console.error('获取数据失败:', error)
        this.error = error.message
      }
    }
  }
}
</script>

<template>
  <div>
    <h2>历史记录测试页面</h2>
    <p>组件已加载</p>
    <button @click="testFetch">测试获取数据</button>
    <div v-if="error">{{ error }}</div>
    <pre v-if="data">{{ data }}</pre>
  </div>
</template>

<style scoped>
.history-test {
  padding: 20px;
}

.debug-panel {
  background: #f5f7fa;
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
}

.work-list {
  margin-top: 20px;
}

.work-item {
  margin-bottom: 30px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
}

.work-item h3 {
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.article-item {
  padding: 10px;
  margin: 10px 0;
  background: #f5f7fa;
  border-radius: 4px;
}

.article-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.article-meta {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
  display: flex;
  gap: 10px;
}

.article-summary {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

button {
  padding: 8px 15px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #66b1ff;
}
</style> 