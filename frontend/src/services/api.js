import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',  // 确保使用后端服务器地址
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加请求拦截器
api.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url)
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 添加响应拦截器
api.interceptors.response.use(
  response => {
    console.log('收到响应:', response.data)
    return response
  },
  error => {
    console.error('响应错误:', error)
    return Promise.reject(error)
  }
)

export const articleService = {
  // 获取文章列表
  async getArticleList() {
    try {
      const response = await api.get('/article/list/')
      return response.data
    } catch (error) {
      console.error('获取文章列表失败:', error)
      throw error
    }
  },

  // 获取文章详情
  async getArticleDetail(articleId) {
    try {
      const response = await api.get(`/article/${articleId}/`)
      return response.data
    } catch (error) {
      console.error('获取文章详情失败:', error)
      throw error
    }
  },

  // 分析文章
  async analyzeArticle(title, content) {
    try {
      const response = await api.post('/article/analyze/', 
        JSON.stringify({ title, content }),
        {
          headers: {
            'Content-Type': 'application/json'
          }
        }
      )
      return response.data
    } catch (error) {
      console.error('分析文章失败:', error)
      throw error
    }
  }
}

export const graphService = {
  // 获取知识图谱数据
  async getGraphData(workName = null) {
    try {
      const url = workName ? `/graph/${workName}/` : '/graph/'
      const response = await api.get(url)
      return response.data
    } catch (error) {
      console.error('获取知识图谱数据失败:', error)
      throw error
    }
  }
}

export default {
  articleService,
  graphService
} 