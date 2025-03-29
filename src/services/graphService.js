import axios from 'axios'

export const graphService = {
  // 获取作品列表
  async getWorks() {
    try {
      const response = await axios.get('/api/works/')
      return response.data
    } catch (error) {
      console.error('获取作品列表失败:', error)
      throw error
    }
  },

  // 获取特定作品的图谱数据
  async getGraphData(workId) {
    try {
      const response = await axios.get(`/api/graph/${workId}/`)
      return response.data
    } catch (error) {
      console.error('获取图谱数据失败:', error)
      throw error
    }
  },

  // 获取节点详情
  async getNodeDetails(nodeId) {
    try {
      const response = await axios.get(`/api/node/${nodeId}/`)
      return response.data
    } catch (error) {
      console.error('获取节点详情失败:', error)
      throw error
    }
  },

  // 获取关系详情
  async getRelationships(nodeId) {
    try {
      const response = await axios.get(`/api/relationships/${nodeId}/`)
      return response.data
    } catch (error) {
      console.error('获取关系详情失败:', error)
      throw error
    }
  }
} 