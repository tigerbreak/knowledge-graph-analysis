import axios from 'axios'

// 创建 axios 实例
const http = axios.create({
  baseURL: '/api',  // 与 vite.config.js 中的代理配置对应
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
http.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url)
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
http.interceptors.response.use(
  response => {
    console.log('收到响应:', response.config.url, response.data)
    return response
  },
  error => {
    console.error('响应错误:', error.config?.url, error.message)
    return Promise.reject(error)
  }
)

export default http 