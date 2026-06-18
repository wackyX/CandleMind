import request from './index'

export function searchStockSymbols(keyword = '') {
  return request({
    url: '/api/stock/symbols',
    method: 'get',
    params: { q: keyword }
  })
}

export function generateStockProphecy(data) {
  return request({
    url: '/api/stock/prophecy',
    method: 'post',
    data
  })
}

export function backtestStockProphecy(data) {
  return request({
    url: '/api/stock/prophecy/backtest',
    method: 'post',
    data
  })
}

export function batchBacktestStockProphecy(data) {
  return request({
    url: '/api/stock/prophecy/backtest/batch',
    method: 'post',
    data
  })
}
