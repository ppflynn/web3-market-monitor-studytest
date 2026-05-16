import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000
})

export function getCoinList() {
  return apiClient.get('/coins')
}

export function getCoinDetail(coinId) {
  return apiClient.get(`/coins/${coinId}`)
}

export function searchCoins(keyword, page, size) {
  return apiClient.get('/coins/search', {
    params: {
      keyword,
      page,
      size
    }
  })
}

export function getCoinHistory(coinId, days = 7) {
  return apiClient.get(`/coins/${coinId}/history`, {
    params: { days },
    timeout: 30000
  })
}

export function getFearGreed() {
  return apiClient.get('/fear-greed')
}
