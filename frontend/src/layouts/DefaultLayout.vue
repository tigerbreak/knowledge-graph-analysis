<template>
  <div class="default-layout">
    <NavBar />
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<script>
import NavBar from '../components/NavBar.vue'

export default {
  name: 'DefaultLayout',
  components: {
    NavBar
  }
}
</script>

<style scoped>
.default-layout {
  min-height: 100vh;  /* 至少铺满视口高度 */
  height: 100%;      /* 可以随内容增长 */
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  width: 100%;
  box-sizing: border-box;
  display: flex;        /* 添加 flex 布局 */
  flex-direction: column;  /* 垂直方向排列 */
  height: 100%;        /* 确保高度传递 */
}
</style> 