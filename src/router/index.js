import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import Home from '../views/Home.vue'
import ArticleAnalysis from '../views/ArticleAnalysis.vue'
import WorkAnalysis from '../components/WorkAnalysis.vue'
import CharacterDetails from '../views/CharacterDetails.vue'
import Events from '../views/Events.vue'
import Factions from '../views/Factions.vue'

console.log('router/index.js 执行')

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: Home
      },
      {
        path: '/article-analysis',
        name: 'ArticleAnalysis',
        component: ArticleAnalysis
      },
      {
        path: '/work-analysis',
        name: 'WorkAnalysis',
        component: WorkAnalysis
      },
      {
        path: '/character-details',
        name: 'CharacterDetails',
        component: () => import('../views/CharacterDetails.vue')
      },
      {
        path: '/events',
        name: 'Events',
        component: Events
      },
      {
        path: '/factions',
        name: 'Factions',
        component: Factions
      }
    ]
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('../components/KnowledgeGraph.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  console.log('路由变化:', to.path)
  next()
})

export default router 