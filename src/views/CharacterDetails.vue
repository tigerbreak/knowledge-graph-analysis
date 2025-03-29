<template>
  <div class="character-details">
    <h2>人物详情</h2>
    
    <!-- 作品选择和搜索区域 -->
    <div class="search-area">
      <el-select v-model="selectedWork" placeholder="选择作品" clearable @change="handleWorkChange">
        <el-option
          v-for="work in works"
          :key="work.id"
          :label="work.name"
          :value="work.id"
        />
      </el-select>
      
      <el-input
        v-model="searchText"
        placeholder="搜索人物"
        clearable
        @input="handleSearch"
        style="width: 200px; margin-left: 10px;"
      >
        <template #suffix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 人物列表 -->
    <div class="character-list">
      <el-table :data="characters" style="width: 100%">
        <el-table-column prop="name" label="人物名称" width="150" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="faction" label="所属势力" width="150" />
        <el-table-column prop="force" label="所属势力(关系)" width="150" />
        <el-table-column prop="work_name" label="所属作品" width="150" v-if="!selectedWork" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const works = ref([])
const characters = ref([])
const selectedWork = ref('')
const searchText = ref('')

// 获取数据的函数
const fetchData = async () => {
  try {
    const params = {}
    if (selectedWork.value) {
      params.work_id = selectedWork.value
    }
    if (searchText.value) {
      params.character_name = searchText.value
    }
    
    const response = await axios.get('/api/character-details/', { params })
    if (response.data.code === 0) {
      characters.value = response.data.data.characters
      if (!works.value.length) {
        works.value = response.data.data.works
      }
    } else {
      ElMessage.error(response.data.message || '获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error('获取数据失败')
  }
}

// 处理作品选择变化
const handleWorkChange = () => {
  fetchData()
}

// 处理搜索输入
const handleSearch = () => {
  fetchData()
}

// 组件挂载时获取初始数据
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.character-details {
  padding: 20px;
}

.search-area {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
}

.character-list {
  margin-top: 20px;
}
</style> 