import { createRouter, createWebHistory } from 'vue-router'
import CoinList from '../views/CoinList.vue'
import CoinDetail from '../views/CoinDetail.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
