<template>
  <nav class="navbar">
    <div class="nav-brand">
      <router-link to="/" class="brand-link">知识图谱分析系统</router-link>
    </div>
    <div class="nav-links">
      <router-link to="/" class="nav-link">首页</router-link>
      <router-link to="/article-analysis" class="nav-link">文章分析</router-link>
      <router-link to="/work-analysis" class="nav-link">人物知识图谱</router-link>
      <router-link to="/character-details" class="nav-link">人物详情</router-link>
      <router-link to="/events" class="nav-link">事件列表</router-link>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'NavBar'
}
</script>

<style scoped>
.navbar {
  background-color: #2c3e50;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: bold;
}

.brand-link {
  color: #ffffff;
  text-decoration: none;
  transition: color 0.3s ease;
}

.brand-link:hover {
  color: #42b983;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-link {
  color: #ffffff;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.nav-link:hover {
  background-color: #42b983;
  color: #ffffff;
}

.router-link-active {
  background-color: #42b983;
  color: #ffffff;
}
</style> 