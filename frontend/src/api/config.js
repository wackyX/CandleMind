import request from './index'

export function getLlmConfig() {
  return request({
    url: '/api/config/llm',
    method: 'get'
  })
}

export function checkLlmConfig() {
  return request({
    url: '/api/config/check-llm',
    method: 'post'
  })
}
