import { createRouter, createWebHistory } from 'vue-router'
import CoinList from '../views/CoinList.vue'
import CoinDetail from '../views/CoinDetail.vue'
import AiAssistant from '../views/AiAssistant.vue'

const routes = [
  {
    path: '/',
    name: 'CoinList',
    component: CoinList
  },
  {
    path: '/coin/:coinId',
    name: 'CoinDetail',
    component: CoinDetail
  },
  {
    path: '/ai',
    name: 'AiAssistant',
    component: AiAssistant
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
