<template>
  <div class="settings-page">
    <el-card class="settings-card">
      <template #header>
        <div class="card-header">
          <span>系统设置</span>
        </div>
      </template>
      
      <el-form :model="settings" label-width="120px">
        <el-form-item label="文本分片大小">
          <el-slider
            v-model="settings.chunkSize"
            :min="1000"
            :max="5000"
            :step="100"
            show-input
            @change="handleChunkSizeChange"
          />
          <div class="slider-tip">
            当前值：{{ settings.chunkSize }} 字符
            <el-tooltip content="设置文本分析时的分片大小，范围1000-5000字符" placement="right">
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'

const settings = ref({
  chunkSize: 5000
})

// 从localStorage加载设置
onMounted(() => {
  const savedChunkSize = localStorage.getItem('chunkSize')
  if (savedChunkSize) {
    settings.value.chunkSize = parseInt(savedChunkSize)
  }
})

// 处理分片大小变化
const handleChunkSizeChange = (value) => {
  localStorage.setItem('chunkSize', value)
  ElMessage.success('设置已保存')
}
</script>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
}

.settings-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slider-tip {
  margin-top: 8px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style> 