<template>
  <div class="stock-page">
    <section v-if="!report && !loading" class="entry-screen">
      <form class="entry-card" @submit.prevent="loadProphecy">
        <div class="entry-logo">
          <img src="/candlemind-icon.svg" alt="烛机 CandleMind" />
        </div>
        <div class="entry-copy">
          <h1>烛机</h1>
          <p>CandleMind。输入 A 股代码，生成真实行情、新闻事件和 DeepSeek 裁决后的未来 K 线路径。</p>
        </div>
        <label class="entry-field" for="entry-stock-symbol">
          <span>股票代码</span>
          <input
            id="entry-stock-symbol"
            v-model="form.symbol"
            list="entry-symbol-list"
            maxlength="6"
            inputmode="numeric"
            autocomplete="off"
            autofocus
          />
          <datalist id="entry-symbol-list">
            <option v-for="item in symbols" :key="item.symbol" :value="item.symbol">
              {{ item.name }}
            </option>
          </datalist>
        </label>
        <div class="entry-options">
          <label class="field" for="entry-stock-horizon">
            <span>预测窗口</span>
            <select id="entry-stock-horizon" v-model.number="form.horizon">
              <option :value="1">1 个交易日</option>
              <option :value="5">5 个交易日</option>
              <option :value="10">10 个交易日</option>
              <option :value="20">20 个交易日</option>
            </select>
          </label>
          <label class="field" for="entry-stock-days">
            <span>样本长度</span>
            <select id="entry-stock-days" v-model.number="form.days">
              <option :value="120">120 日</option>
              <option :value="180">180 日</option>
              <option :value="240">240 日</option>
              <option :value="320">320 日</option>
            </select>
          </label>
        </div>
        <label class="toggle-field entry-toggle">
          <input v-model="form.includeEvents" type="checkbox" />
          <span>拉取近期新闻和公告事件</span>
        </label>
        <label class="toggle-field entry-toggle">
          <input v-model="form.useLlm" type="checkbox" />
          <span>启用 DeepSeek 裁决和预言</span>
        </label>
        <button class="primary-button entry-submit" type="submit">
          开始预言
        </button>
        <p v-if="error" class="entry-error">{{ error }}</p>
      </form>
    </section>

    <section v-else-if="loading" class="entry-screen loading-screen">
      <div class="entry-card loading-card">
        <div class="entry-logo scanning">
          <img src="/candlemind-icon.svg" alt="烛机 CandleMind" />
        </div>
        <div class="entry-copy">
          <h1>烛机正在推演</h1>
          <p>{{ form.symbol }} 的行情、事件和模型裁决正在汇合，完成后会一次性渲染完整结果。</p>
        </div>
        <div class="loading-stack">
          <div
            v-for="(step, index) in loadingSteps"
            :key="step"
            :class="['loading-step', { active: index === loadingStepIndex, done: index < loadingStepIndex }]"
          >
            <span class="step-indicator">
              <i v-if="index === loadingStepIndex" class="step-spinner"></i>
              <b v-else>{{ index + 1 }}</b>
            </span>
            <strong>{{ step }}</strong>
          </div>
        </div>
      </div>
    </section>

    <template v-else>
    <header class="command-bar">
      <button class="brand-button" @click="router.push('/')">
        <span class="brand-mark">
          <img src="/candlemind-icon.svg" alt="烛机 CandleMind" />
        </span>
        <span class="brand-copy">
          <strong>烛机</strong>
          <small>CandleMind A股日K终端</small>
        </span>
      </button>
      <div class="market-status">
        <span>A-SHARE</span>
        <span>1D</span>
        <span>{{ report ? providerLabel(report.provider) : '等待行情' }}</span>
      </div>
      <nav class="header-actions">
        <button class="ghost-button" @click="loadProphecy" :disabled="loading">
          {{ loading ? '推演中' : '刷新推演' }}
        </button>
      </nav>
    </header>

    <main class="terminal-grid">
      <aside class="side-console">
        <section class="surface control-panel">
          <div class="panel-title">A股日K推演</div>
          <label class="field" for="stock-symbol">
            <span>股票代码</span>
            <input id="stock-symbol" v-model="form.symbol" list="symbol-list" maxlength="6" inputmode="numeric" />
            <datalist id="symbol-list">
              <option v-for="item in symbols" :key="item.symbol" :value="item.symbol">
                {{ item.name }}
              </option>
            </datalist>
          </label>
          <label class="field" for="stock-horizon">
            <span>预测窗口</span>
            <select id="stock-horizon" v-model.number="form.horizon">
              <option :value="1">1 个交易日</option>
              <option :value="5">5 个交易日</option>
              <option :value="10">10 个交易日</option>
              <option :value="20">20 个交易日</option>
            </select>
          </label>
          <label class="field" for="stock-days">
            <span>样本长度</span>
            <select id="stock-days" v-model.number="form.days">
              <option :value="120">120 日</option>
              <option :value="180">180 日</option>
              <option :value="240">240 日</option>
              <option :value="320">320 日</option>
            </select>
          </label>
          <label class="toggle-field">
            <input v-model="form.includeEvents" type="checkbox" />
            <span>拉取近期新闻和公告事件</span>
          </label>
          <label class="toggle-field">
            <input v-model="form.useLlm" type="checkbox" />
            <span>启用 LLM 裁决和预言</span>
          </label>
          <button class="primary-button" @click="loadProphecy" :disabled="loading">
            {{ loading ? '正在生成' : '生成预言' }}
          </button>
          <p class="micro-copy">K线优先来自东方财富，必要时用新浪历史行情和东方财富实时行情兜底。结果仅用于研究和复盘。</p>
        </section>

        <section v-if="report" class="surface compact market-snapshot">
          <div class="panel-title">行情快照</div>
          <div class="metric-grid">
            <div>
              <span>收盘</span>
              <strong>{{ report.snapshot.close }}</strong>
            </div>
            <div>
              <span>涨跌</span>
              <strong :class="signedClass(report.snapshot.changePct)">{{ report.snapshot.changePct }}%</strong>
            </div>
            <div>
              <span>RSI14</span>
              <strong>{{ report.snapshot.rsi14 }}</strong>
            </div>
            <div>
              <span>ATR14</span>
              <strong>{{ report.snapshot.atr14 }}</strong>
            </div>
            <div class="provider-cell">
              <span>行情源</span>
              <strong>{{ providerLabel(report.provider) }}</strong>
            </div>
          </div>
        </section>
      </aside>

      <section class="workbench">
        <div v-if="error" class="error-strip">{{ error }}</div>
        <div v-if="loading && !report" class="surface chart-shell loading-shell">
          <div class="skeleton-line wide"></div>
          <div class="skeleton-chart"></div>
        </div>

        <template v-if="report">
          <section class="surface chart-shell">
            <div class="stage-head">
              <div class="asset-block">
                <div class="asset-line">
                  <span>{{ report.market }} {{ report.period }}</span>
                  <strong>{{ report.symbol }}</strong>
                </div>
                <h1>{{ report.name }} 烛机预言</h1>
                <p>未来 {{ report.horizon }} 个交易日，基于真实日K、近期新闻公告和相似形态生成单一路径。</p>
              </div>
              <div v-if="forecastSummary" :class="['forecast-panel', directionTone(report.forecast.direction)]">
                <span>主预言</span>
                <strong>{{ forecastSummary.direction }} {{ report.forecast.probability }}%</strong>
                <div class="forecast-stats">
                  <div>
                    <small>预估收盘</small>
                    <b>{{ forecastSummary.close }}</b>
                  </div>
                  <div>
                    <small>区间变化</small>
                    <b :class="signedClass(forecastSummary.deltaPct)">{{ forecastSummary.deltaPct }}%</b>
                  </div>
                </div>
              </div>
            </div>

            <div class="chart-frame">
              <svg class="kline-chart" :viewBox="`0 0 ${chart.width} ${chart.height}`" role="img">
              <g class="grid">
                <line
                  v-for="tick in chart.priceTicks"
                  :key="tick.value"
                  :x1="chart.padding.left"
                  :x2="chart.width - chart.padding.right"
                  :y1="tick.y"
                  :y2="tick.y"
                />
              </g>
              <g>
                <text
                  v-for="tick in chart.priceTicks"
                  :key="`label-${tick.value}`"
                  class="axis-label"
                  :x="chart.width - chart.padding.right + 8"
                  :y="tick.y + 4"
                >
                  {{ tick.value }}
                </text>
              </g>
              <rect
                v-if="chart.forecastBand"
                class="forecast-band"
                :x="chart.forecastBand.x"
                :y="chart.padding.top"
                :width="chart.forecastBand.width"
                :height="chart.height - chart.padding.top - chart.padding.bottom"
              />
              <line
                v-if="chart.forecastBand"
                class="forecast-divider"
                :x1="chart.forecastBand.x"
                :x2="chart.forecastBand.x"
                :y1="chart.padding.top"
                :y2="chart.height - chart.padding.bottom"
              />
              <text
                v-if="chart.forecastBand"
                class="forecast-label"
                :x="chart.forecastBand.x + 8"
                :y="chart.padding.top + 18"
              >
                预言区
              </text>
              <g class="candles">
                <g v-for="item in chart.candles" :key="item.date">
                  <line :x1="item.x" :x2="item.x" :y1="item.highY" :y2="item.lowY" :class="item.up ? 'up' : 'down'" />
                  <rect
                    :x="item.x - item.width / 2"
                    :y="Math.min(item.openY, item.closeY)"
                    :width="item.width"
                    :height="Math.max(1, Math.abs(item.closeY - item.openY))"
                    :class="item.up ? 'up-fill' : 'down-fill'"
                  />
                </g>
              </g>
              <g class="forecast-candles">
                <g v-for="item in chart.forecastCandles" :key="`forecast-${item.day}`">
                  <line :x1="item.x" :x2="item.x" :y1="item.highY" :y2="item.lowY" :class="item.up ? 'forecast-up' : 'forecast-down'" />
                  <rect
                    :x="item.x - item.width / 2"
                    :y="Math.min(item.openY, item.closeY)"
                    :width="item.width"
                    :height="Math.max(2, Math.abs(item.closeY - item.openY))"
                    :class="item.up ? 'forecast-up-fill' : 'forecast-down-fill'"
                  />
                </g>
              </g>
              <path class="ma-line ma5" :d="chart.ma5Path" />
              <path class="ma-line ma20" :d="chart.ma20Path" />
              <line class="level support" :x1="chart.padding.left" :x2="chart.width - chart.padding.right" :y1="chart.supportY" :y2="chart.supportY" />
              <line class="level resistance" :x1="chart.padding.left" :x2="chart.width - chart.padding.right" :y1="chart.resistanceY" :y2="chart.resistanceY" />
              </svg>
              <div class="chart-stamp">
                <span>生成时间</span>
                <strong>{{ formatDateTime(report.generatedAt) }}</strong>
              </div>
            </div>

            <div class="legend-row">
              <span><i class="dot up-dot"></i>上涨K线</span>
              <span><i class="dot down-dot"></i>下跌K线</span>
              <span><i class="line ma5-dot"></i>MA5</span>
              <span><i class="line ma20-dot"></i>MA20</span>
              <span><i class="dot prophecy-dot"></i>单一路径预言K线</span>
            </div>
          </section>

          <section class="scenario-strip">
            <article
              v-for="scenario in report.scenarios"
              :key="scenario.key"
              :class="['scenario-card', scenarioTone(scenario.key), { active: report.forecast?.direction === scenario.key }]"
            >
              <div class="scenario-top">
                <span>{{ scenario.name }}</span>
                <strong>{{ scenario.probability }}%</strong>
              </div>
              <div class="probability-bar">
                <span :style="{ width: `${scenario.probability}%` }"></span>
              </div>
              <p>{{ scenario.description }}</p>
              <small>{{ scenario.trigger }}</small>
            </article>
          </section>

          <section v-if="report.llmProphecy" class="surface llm-panel">
            <div class="panel-title">LLM 裁决层</div>
            <div :class="['llm-status', report.llmProphecy.status === 'ok' ? 'ok' : 'fallback']">
              <span>{{ llmStatusText(report.llmProphecy.status) }}</span>
              <strong>{{ report.llmProphecy.summary }}</strong>
            </div>
            <div v-if="report.llmProphecy.status === 'ok'" class="llm-columns">
              <div>
                <span>核心依据</span>
                <p v-for="item in report.llmProphecy.reasons" :key="`reason-${item}`">{{ item }}</p>
              </div>
              <div>
                <span>风险</span>
                <p v-for="item in report.llmProphecy.risks" :key="`risk-${item}`">{{ item }}</p>
              </div>
              <div>
                <span>失效条件</span>
                <p v-for="item in report.llmProphecy.invalidations" :key="`invalid-${item}`">{{ item }}</p>
              </div>
            </div>
          </section>

          <section class="intel-grid event-layout">
            <article class="surface wide-panel">
              <div class="panel-title">近期新闻与公告事件</div>
              <div v-if="report.events?.events?.length" class="event-list">
                <a
                  v-for="event in report.events.events"
                  :key="`${event.type}-${event.title}`"
                  class="event-row"
                  :href="event.url"
                  target="_blank"
                >
                  <div class="event-meta">
                    <span :class="['event-type', event.type]">{{ event.type === 'announcement' ? '公告' : '新闻' }}</span>
                    <span>{{ formatEventTime(event.datetime) }}</span>
                    <span>{{ event.source }}</span>
                  </div>
                  <strong>{{ event.title }}</strong>
                  <p v-if="event.summary">{{ event.summary }}</p>
                  <div class="event-tags">
                    <span :class="['sentiment-tag', event.sentiment]">{{ sentimentText(event.sentiment) }}</span>
                    <span>重要性 {{ event.importance }}</span>
                  </div>
                </a>
              </div>
              <p v-else class="empty-copy">没有获取到近期新闻或公告。</p>
            </article>

            <article class="surface signal-panel">
              <div class="panel-title">事件信号</div>
              <div class="signal-card">
                <span>{{ report.events?.signal?.label || '未启用' }}</span>
                <strong :class="signedClass(report.events?.signal?.score)">
                  {{ report.events?.signal?.score ?? 0 }}
                </strong>
                <p>{{ report.events?.signal?.summary || '新闻公告事件未参与本次推演。' }}</p>
                <div v-if="report.events?.meta" class="source-times">
                  <div>
                    <span>新闻最新</span>
                    <strong>{{ formatEventTime(report.events.meta.latestNewsAt) }}</strong>
                  </div>
                  <div>
                    <span>公告最新</span>
                    <strong>{{ formatEventTime(report.events.meta.latestAnnouncementAt) }}</strong>
                  </div>
                </div>
              </div>
            </article>
          </section>

          <section class="intel-grid">
            <article class="surface wide-panel">
              <div class="panel-title">Agent 辩论摘要</div>
              <div class="agent-list">
                <div v-for="agent in report.agents" :key="agent.role" class="agent-row">
                  <div>
                    <span>{{ agent.role }}</span>
                    <strong>{{ agent.stance }}</strong>
                  </div>
                  <p>{{ agent.message }}</p>
                </div>
              </div>
            </article>

            <article class="surface backtest-panel">
              <div class="panel-title">相似形态回测</div>
              <div class="backtest-number">
                <span>上涨概率</span>
                <strong>{{ report.analog.upProbability ?? '--' }}%</strong>
              </div>
              <div class="metric-grid">
                <div>
                  <span>样本</span>
                  <strong>{{ report.analog.sampleSize }}</strong>
                </div>
                <div>
                  <span>均值收益</span>
                  <strong :class="signedClass(report.analog.avgForwardReturn)">
                    {{ report.analog.avgForwardReturn ?? '--' }}%
                  </strong>
                </div>
              </div>
            </article>
          </section>

          <section class="surface seed-panel">
            <div class="panel-title">Stock Seed Report</div>
            <pre>{{ report.seedReport }}</pre>
          </section>
        </template>
      </section>
    </main>
    </template>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { generateStockProphecy, searchStockSymbols } from '../api/stock'

const router = useRouter()
const loading = ref(false)
const loadingStepIndex = ref(0)
let loadingTimer = null
const error = ref('')
const report = ref(null)
const symbols = ref([])
const loadingSteps = [
  '连接东方财富并拉取近期日K',
  '计算均线、RSI、ATR和相似形态',
  '抓取近期新闻和公告事件',
  '整理种子报告并请求 DeepSeek',
  '生成单一路径预言K线',
  '校验风险边界并渲染结果'
]
const form = reactive({
  symbol: '600519',
  horizon: 5,
  days: 180,
  includeEvents: true,
  useLlm: true
})

const chart = computed(() => {
  if (!report.value) {
    return { width: 980, height: 440, padding: { left: 56, right: 62, top: 26, bottom: 36 }, priceTicks: [], candles: [], forecastCandles: [], forecastBand: null }
  }
  const width = 980
  const height = 440
  const padding = { left: 56, right: 62, top: 26, bottom: 36 }
  const visibleCandles = report.value.candles.slice(-88)
  const forecastSource = report.value.forecast?.candles || []
  const projectedValues = forecastSource.flatMap((item) => [item.high, item.low, item.open, item.close])
  const allPrices = visibleCandles.flatMap((item) => [item.high, item.low]).concat(projectedValues)
  const minPrice = Math.min(...allPrices) * 0.985
  const maxPrice = Math.max(...allPrices) * 1.015
  const innerWidth = width - padding.left - padding.right
  const innerHeight = height - padding.top - padding.bottom
  const totalSlots = visibleCandles.length + report.value.paths.length + 2
  const xStep = innerWidth / totalSlots
  const candleWidth = Math.max(3, Math.min(9, xStep * 0.58))
  const y = (value) => padding.top + (maxPrice - value) / (maxPrice - minPrice) * innerHeight
  const x = (index) => padding.left + index * xStep + xStep
  const lastIndex = visibleCandles.length - 1
  const candles = visibleCandles.map((item, index) => ({
    ...item,
    x: x(index),
    width: candleWidth,
    openY: y(item.open),
    closeY: y(item.close),
    highY: y(item.high),
    lowY: y(item.low),
    up: item.close >= item.open
  }))
  const forecastCandles = []
  forecastSource.forEach((item, index) => {
    forecastCandles.push({
      ...item,
      x: x(lastIndex + index + 1),
      width: candleWidth,
      openY: y(item.open),
      closeY: y(item.close),
      highY: y(item.high),
      lowY: y(item.low),
      up: item.close >= item.open
    })
  })
  const visibleIndicators = report.value.indicators.slice(-88)
  const makeLine = (values, offset = 0) => values
    .map((value, index) => value == null ? null : `${index === 0 || values[index - 1] == null ? 'M' : 'L'} ${x(index + offset).toFixed(2)} ${y(value).toFixed(2)}`)
    .filter(Boolean)
    .join(' ')
  const ticks = Array.from({ length: 5 }, (_, index) => {
    const value = minPrice + (maxPrice - minPrice) * index / 4
    return { value: value.toFixed(2), y: y(value) }
  }).reverse()
  return {
    width,
    height,
    padding,
    priceTicks: ticks,
    candles,
    forecastCandles,
    forecastBand: forecastCandles.length
      ? {
          x: forecastCandles[0].x - xStep / 2,
          width: xStep * (forecastCandles.length + 0.9)
        }
      : null,
    ma5Path: makeLine(visibleIndicators.map((item) => item.ma5)),
    ma20Path: makeLine(visibleIndicators.map((item) => item.ma20)),
    supportY: y(report.value.snapshot.support),
    resistanceY: y(report.value.snapshot.resistance)
  }
})

const forecastSummary = computed(() => {
  const forecast = report.value?.forecast
  const candles = forecast?.candles || []
  if (!forecast || !candles.length || !report.value?.snapshot) return null
  const last = candles[candles.length - 1]
  const base = Number(report.value.snapshot.close)
  const close = Number(last.close)
  const deltaPct = base ? ((close - base) / base * 100).toFixed(2) : '0.00'
  return {
    direction: directionLabel(forecast.direction),
    close: close.toFixed(2),
    deltaPct
  }
})

const loadSymbols = async () => {
  const res = await searchStockSymbols()
  symbols.value = res.data
}

const loadProphecy = async () => {
  loading.value = true
  report.value = null
  error.value = ''
  startLoadingSteps()
  try {
    const res = await generateStockProphecy({
      symbol: form.symbol,
      horizon: form.horizon,
      days: form.days,
      provider: 'eastmoney',
      includeEvents: form.includeEvents,
      useLlm: form.useLlm
    })
    report.value = res.data
  } catch (err) {
    error.value = err.message || '推演失败'
  } finally {
    stopLoadingSteps()
    loading.value = false
  }
}

const startLoadingSteps = () => {
  stopLoadingSteps()
  loadingStepIndex.value = 0
  loadingTimer = window.setInterval(() => {
    loadingStepIndex.value = Math.min(loadingSteps.length - 1, loadingStepIndex.value + 1)
  }, 1800)
}

const stopLoadingSteps = () => {
  if (loadingTimer) {
    window.clearInterval(loadingTimer)
    loadingTimer = null
  }
}

const signedClass = (value) => {
  if (value == null) return ''
  return Number(value) >= 0 ? 'positive' : 'negative'
}

const directionLabel = (value) => {
  const map = {
    bull: '看多',
    bear: '看空',
    neutral: '震荡'
  }
  return map[value] || '观望'
}

const directionTone = (value) => {
  const map = {
    bull: 'tone-bull',
    bear: 'tone-bear',
    neutral: 'tone-neutral'
  }
  return map[value] || 'tone-neutral'
}

const scenarioTone = directionTone

const formatDateTime = (value) => new Date(value).toLocaleString('zh-CN', {
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
})

const formatEventTime = (value) => {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value.slice(0, 16)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const sentimentText = (value) => {
  const map = {
    positive: '偏多',
    negative: '偏空',
    neutral: '中性'
  }
  return map[value] || '中性'
}

const providerLabel = (value) => {
  const map = {
    eastmoney: '东方财富',
    'sina+eastmoney_realtime': '新浪历史+东财实时',
    sina: '新浪历史',
    demo: 'Demo'
  }
  return map[value] || value || '--'
}

const llmStatusText = (value) => {
  const map = {
    ok: '已参与',
    failed: '已回退',
    missing_config: '未配置',
    disabled: '未启用'
  }
  return map[value] || value || '未知'
}

onMounted(() => {
  loadSymbols()
})

onBeforeUnmount(() => {
  stopLoadingSteps()
})
</script>

<style scoped>
.stock-page {
  min-height: 100dvh;
  color: #dce7e9;
  background:
    linear-gradient(90deg, rgba(74, 222, 255, 0.05) 1px, transparent 1px),
    linear-gradient(0deg, rgba(74, 222, 255, 0.035) 1px, transparent 1px),
    linear-gradient(135deg, #071019 0%, #0a1016 48%, #070b12 100%);
  background-size: 56px 56px, 56px 56px, auto;
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  overflow-x: hidden;
}

.stock-page::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 20% 0%, rgba(54, 211, 255, 0.12), transparent 32%),
    radial-gradient(circle at 88% 14%, rgba(255, 74, 113, 0.07), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.035), transparent 20%, rgba(0, 0, 0, 0.22));
  z-index: 0;
}

.stock-page::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(255,255,255,0.035) 50%, rgba(0,0,0,0.025) 50%);
  background-size: 100% 5px;
  opacity: 0.16;
  z-index: 1;
}

.command-bar,
.terminal-grid {
  position: relative;
  z-index: 2;
}

.entry-screen {
  position: relative;
  z-index: 2;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 28px;
}

.entry-card {
  width: min(620px, 100%);
  display: grid;
  gap: 18px;
  padding: 26px;
  border: 1px solid rgba(90, 203, 222, 0.22);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(11, 23, 33, 0.94), rgba(7, 13, 20, 0.96));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.065), 0 28px 70px rgba(0, 0, 0, 0.34);
}

.entry-logo {
  width: 74px;
  height: 74px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  box-shadow: 0 0 36px rgba(45, 212, 255, 0.2);
}

.entry-logo img {
  width: 74px;
  height: 74px;
  display: block;
}

.entry-logo.scanning {
  animation: pulseScan 1.8s ease-in-out infinite;
}

.entry-copy {
  display: grid;
  gap: 10px;
}

.entry-copy h1 {
  font-size: clamp(36px, 8vw, 64px);
}

.entry-copy p {
  max-width: 52ch;
  margin: 0;
  color: #a9bdc3;
  font-size: 15px;
  line-height: 1.7;
}

.entry-field {
  display: grid;
  gap: 8px;
}

.entry-field span {
  color: #78909a;
  font-size: 12px;
  font-weight: 850;
}

.entry-field input {
  height: 58px;
  font: 900 24px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.08em;
}

.entry-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.entry-toggle {
  margin: 0;
}

.entry-submit {
  height: 48px;
  font-size: 15px;
}

.entry-error {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid rgba(255, 74, 113, 0.62);
  border-radius: 6px;
  background: rgba(57, 14, 24, 0.9);
  color: #ff9aac;
  font-size: 13px;
  font-weight: 750;
}

.loading-card {
  width: min(700px, 100%);
}

.loading-stack {
  display: grid;
  gap: 9px;
  margin-top: 4px;
}

.loading-step {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr);
  align-items: center;
  gap: 10px;
  min-height: 42px;
  padding: 8px 10px;
  border: 1px solid rgba(90, 203, 222, 0.12);
  border-radius: 6px;
  background: rgba(3, 10, 16, 0.36);
  color: #78909a;
}

.step-indicator {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  border: 1px solid rgba(90, 203, 222, 0.18);
  font: 850 11px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.step-indicator b {
  font: inherit;
}

.step-spinner {
  width: 13px;
  height: 13px;
  border-radius: 50%;
  border: 2px solid rgba(24, 16, 3, 0.28);
  border-top-color: #181003;
  animation: spin 0.78s linear infinite;
}

.loading-step strong {
  font-size: 13px;
  line-height: 1.35;
}

.loading-step.done {
  color: #a9bdc3;
}

.loading-step.done .step-indicator {
  color: #031118;
  background: #82f3ff;
}

.loading-step.active {
  color: #effcff;
  border-color: rgba(255, 202, 91, 0.42);
  box-shadow: inset 3px 0 0 rgba(255, 202, 91, 0.9);
}

.loading-step.active .step-indicator {
  color: #181003;
  background: #ffca5b;
}

.command-bar {
  height: 72px;
  display: grid;
  grid-template-columns: minmax(190px, 1fr) auto minmax(190px, 1fr);
  align-items: center;
  gap: 16px;
  padding: 0 22px;
  border-bottom: 1px solid rgba(90, 203, 222, 0.24);
  background: rgba(6, 12, 19, 0.88);
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 5;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
}

.brand-button,
.ghost-button,
.primary-button,
.github-link {
  font-family: inherit;
  letter-spacing: 0;
}

.brand-button {
  justify-self: start;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  border: 0;
  background: transparent;
  color: #f0fbfc;
  cursor: pointer;
  min-width: 0;
}

.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  box-shadow: 0 0 26px rgba(45, 212, 255, 0.18);
}

.brand-mark img {
  width: 38px;
  height: 38px;
  display: block;
}

.brand-copy {
  display: grid;
  gap: 2px;
  text-align: left;
}

.brand-copy strong {
  font-size: 15px;
  line-height: 1.1;
}

.brand-copy small {
  color: #78909a;
  font-size: 11px;
  font-weight: 700;
}

.market-status {
  justify-self: center;
  display: grid;
  grid-template-columns: repeat(3, auto);
  align-items: center;
  gap: 1px;
  overflow: hidden;
  border: 1px solid rgba(90, 203, 222, 0.24);
  border-radius: 6px;
  background: rgba(7, 18, 27, 0.72);
}

.market-status span {
  min-width: 72px;
  height: 32px;
  display: grid;
  place-items: center;
  padding: 0 10px;
  color: #a7c3ca;
  background: rgba(255,255,255,0.025);
  font: 800 11px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: nowrap;
}

.header-actions {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 10px;
}

.ghost-button,
.github-link,
.primary-button {
  height: 38px;
  border-radius: 6px;
  padding: 0 14px;
  font-size: 13px;
  font-weight: 850;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, color 0.16s ease;
}

.ghost-button,
.github-link {
  border: 1px solid rgba(90, 203, 222, 0.3);
  background: rgba(8, 20, 30, 0.72);
  color: #c9e6ea;
}

.ghost-button:hover,
.github-link:hover {
  border-color: rgba(130, 243, 255, 0.72);
  color: #ffffff;
  background: rgba(16, 36, 48, 0.88);
}

.primary-button {
  width: 100%;
  border: 1px solid rgba(130, 243, 255, 0.9);
  background: linear-gradient(180deg, #9af7ff, #31c9e6);
  color: #031118;
  box-shadow: 0 14px 34px rgba(49, 201, 230, 0.18), inset 0 1px 0 rgba(255,255,255,0.45);
}

.primary-button:active,
.ghost-button:active,
.github-link:active {
  transform: translateY(1px);
}

button:disabled {
  opacity: 0.58;
  cursor: not-allowed;
}

.terminal-grid {
  display: grid;
  grid-template-columns: 316px minmax(0, 1fr);
  gap: 16px;
  width: min(1540px, calc(100% - 32px));
  margin: 16px auto 26px;
}

.side-console,
.workbench {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.surface,
.scenario-card {
  position: relative;
  border: 1px solid rgba(90, 203, 222, 0.18);
  border-radius: 6px;
  background: linear-gradient(180deg, rgba(11, 23, 33, 0.92), rgba(7, 13, 20, 0.94));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.055), 0 18px 45px rgba(0, 0, 0, 0.22);
}

.surface::before,
.scenario-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(130, 243, 255, 0.58), transparent);
  opacity: 0.7;
  pointer-events: none;
}

.surface {
  padding: 16px;
}

.panel-title {
  margin-bottom: 14px;
  color: #82f3ff;
  font: 900 12px/1.2 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.field {
  display: grid;
  gap: 7px;
  margin-bottom: 14px;
}

.field span,
.metric-grid span,
.backtest-number span,
.source-times span,
.forecast-panel span,
.forecast-stats small {
  color: #78909a;
  font-size: 12px;
  font-weight: 750;
}

input,
select {
  width: 100%;
  height: 42px;
  border: 1px solid rgba(90, 203, 222, 0.25);
  border-radius: 6px;
  padding: 0 11px;
  color: #effcff;
  background: rgba(3, 10, 16, 0.78);
  font-family: inherit;
  outline: none;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}

input:focus,
select:focus {
  border-color: rgba(130, 243, 255, 0.9);
  box-shadow: 0 0 0 3px rgba(49, 201, 230, 0.12);
}

select option {
  background: #08131d;
  color: #effcff;
}

.toggle-field {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 6px 0 16px;
  color: #b6c9ce;
  font-size: 13px;
  font-weight: 750;
}

.toggle-field input {
  width: 16px;
  height: 16px;
  accent-color: #31c9e6;
}

.micro-copy {
  margin: 12px 0 0;
  color: #78909a;
  font-size: 12px;
  line-height: 1.65;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.metric-grid div {
  min-height: 66px;
  display: grid;
  align-content: space-between;
  gap: 8px;
  padding: 10px;
  border: 1px solid rgba(90, 203, 222, 0.13);
  border-radius: 6px;
  background: rgba(3, 10, 16, 0.48);
}

.metric-grid strong {
  color: #effcff;
  font: 850 18px/1.05 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-word;
}

.provider-cell {
  grid-column: 1 / -1;
}

.error-strip {
  padding: 12px 14px;
  border: 1px solid rgba(255, 74, 113, 0.62);
  border-radius: 6px;
  background: rgba(57, 14, 24, 0.9);
  color: #ff9aac;
  font-size: 13px;
  font-weight: 750;
}

.chart-shell {
  padding: 14px;
}

.stage-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(250px, 340px);
  gap: 16px;
  align-items: stretch;
  margin-bottom: 12px;
}

.asset-block {
  min-width: 0;
  display: grid;
  align-content: center;
  gap: 6px;
}

.asset-line {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #78909a;
  font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.asset-line strong {
  color: #effcff;
  font-size: 14px;
}

h1 {
  margin: 0;
  color: #f5fdff;
  font-size: clamp(24px, 3vw, 38px);
  line-height: 1.05;
  letter-spacing: 0;
}

.asset-block p {
  max-width: 68ch;
  margin: 0;
  color: #94aeb5;
  font-size: 13px;
  line-height: 1.6;
}

.forecast-panel {
  display: grid;
  gap: 12px;
  min-height: 122px;
  padding: 14px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(3, 10, 16, 0.64);
}

.forecast-panel strong {
  color: #f5fdff;
  font-size: 26px;
  line-height: 1;
}

.forecast-panel.tone-bull {
  border-color: rgba(255, 74, 113, 0.44);
  box-shadow: inset 3px 0 0 rgba(255, 74, 113, 0.88);
}

.forecast-panel.tone-bear {
  border-color: rgba(49, 201, 230, 0.46);
  box-shadow: inset 3px 0 0 rgba(49, 201, 230, 0.9);
}

.forecast-panel.tone-neutral {
  border-color: rgba(255, 202, 91, 0.42);
  box-shadow: inset 3px 0 0 rgba(255, 202, 91, 0.88);
}

.forecast-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.forecast-stats div {
  display: grid;
  gap: 5px;
  min-width: 0;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.08);
}

.forecast-stats b {
  color: #effcff;
  font: 850 16px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.chart-frame {
  position: relative;
  min-width: 0;
}

.kline-chart {
  width: 100%;
  height: auto;
  min-height: 360px;
  display: block;
  border: 1px solid rgba(90, 203, 222, 0.18);
  border-radius: 6px;
  background:
    linear-gradient(90deg, rgba(90, 203, 222, 0.055) 1px, transparent 1px),
    linear-gradient(0deg, rgba(90, 203, 222, 0.04) 1px, transparent 1px),
    #040a11;
  background-size: 52px 52px, 52px 52px, auto;
  box-shadow: inset 0 0 44px rgba(49, 201, 230, 0.045);
}

.chart-stamp {
  position: absolute;
  right: 12px;
  top: 12px;
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid rgba(90, 203, 222, 0.18);
  background: rgba(4, 10, 17, 0.78);
  backdrop-filter: blur(10px);
}

.chart-stamp span {
  color: #78909a;
  font-size: 11px;
}

.chart-stamp strong {
  color: #dce7e9;
  font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.grid line {
  stroke: rgba(148, 174, 181, 0.18);
}

.axis-label,
.forecast-label {
  fill: #78909a;
  font-size: 11px;
  font-weight: 800;
}

.forecast-label {
  fill: #ffca5b;
}

.up,
.up-fill {
  stroke: #ff4a71;
}

.up-fill {
  fill: #ff4a71;
}

.down,
.down-fill {
  stroke: #31c9e6;
}

.down-fill {
  fill: #31c9e6;
}

.forecast-band {
  fill: rgba(255, 202, 91, 0.055);
}

.forecast-divider {
  stroke: rgba(255, 202, 91, 0.86);
  stroke-width: 1.4;
  stroke-dasharray: 5 5;
}

.forecast-up,
.forecast-down {
  stroke-width: 2;
}

.forecast-up {
  stroke: #ff4a71;
}

.forecast-down {
  stroke: #31c9e6;
}

.forecast-up-fill,
.forecast-down-fill {
  stroke-width: 1;
  opacity: 0.8;
}

.forecast-up-fill {
  fill: #ff4a71;
  stroke: #ff4a71;
}

.forecast-down-fill {
  fill: #31c9e6;
  stroke: #31c9e6;
}

.ma-line,
.level {
  fill: none;
  stroke-width: 1.8;
}

.ma5 {
  stroke: #ffca5b;
}

.ma20 {
  stroke: #82f3ff;
}

.support,
.resistance {
  stroke: rgba(220, 231, 233, 0.55);
  stroke-width: 1;
  stroke-dasharray: 3 5;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 11px;
  color: #78909a;
  font-size: 12px;
  font-weight: 750;
}

.dot,
.line {
  display: inline-block;
  margin-right: 6px;
  vertical-align: middle;
}

.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.line {
  width: 18px;
  height: 2px;
}

.up-dot {
  background: #ff4a71;
}

.down-dot {
  background: #31c9e6;
}

.ma5-dot {
  background: #ffca5b;
}

.ma20-dot {
  background: #82f3ff;
}

.prophecy-dot {
  background: #ffca5b;
  box-shadow: 0 0 12px rgba(255, 202, 91, 0.42);
}

.scenario-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.scenario-card {
  min-height: 146px;
  padding: 14px;
  overflow: hidden;
}

.scenario-card.active {
  border-color: rgba(255, 202, 91, 0.58);
  background: linear-gradient(180deg, rgba(25, 24, 20, 0.95), rgba(8, 13, 19, 0.94));
}

.scenario-card.tone-bull.active {
  box-shadow: inset 3px 0 0 rgba(255, 74, 113, 0.9), 0 18px 45px rgba(0,0,0,0.22);
}

.scenario-card.tone-bear.active {
  box-shadow: inset 3px 0 0 rgba(49, 201, 230, 0.9), 0 18px 45px rgba(0,0,0,0.22);
}

.scenario-card.tone-neutral.active {
  box-shadow: inset 3px 0 0 rgba(255, 202, 91, 0.9), 0 18px 45px rgba(0,0,0,0.22);
}

.scenario-top {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 10px;
  color: #dce7e9;
  font-size: 13px;
  font-weight: 850;
}

.scenario-top strong {
  color: #effcff;
  font: 900 28px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.probability-bar {
  height: 2px;
  margin: 12px 0 11px;
  background: transparent;
  overflow: hidden;
}

.probability-bar span {
  display: block;
  height: 100%;
  background: #82f3ff;
}

.scenario-card.tone-bull .probability-bar span {
  background: #ff4a71;
}

.scenario-card.tone-bear .probability-bar span {
  background: #31c9e6;
}

.scenario-card.tone-neutral .probability-bar span {
  background: #ffca5b;
}

.scenario-card p,
.agent-row p,
.event-row p,
.signal-card p,
.empty-copy {
  margin: 0;
  color: #a9bdc3;
  font-size: 13px;
  line-height: 1.55;
}

.scenario-card small {
  display: block;
  margin-top: 10px;
  color: #78909a;
  font-size: 12px;
  line-height: 1.45;
}

.llm-panel {
  display: grid;
  gap: 12px;
}

.llm-status {
  display: grid;
  gap: 7px;
  padding: 12px;
  border: 1px solid rgba(90, 203, 222, 0.14);
  border-radius: 6px;
  background: rgba(3, 10, 16, 0.42);
}

.llm-status.ok {
  border-color: rgba(130, 243, 255, 0.34);
  box-shadow: inset 3px 0 0 rgba(49, 201, 230, 0.9);
}

.llm-status.fallback {
  border-color: rgba(255, 202, 91, 0.34);
  box-shadow: inset 3px 0 0 rgba(255, 202, 91, 0.9);
}

.llm-status span,
.llm-columns span {
  color: #78909a;
  font-size: 12px;
  font-weight: 850;
}

.llm-status strong {
  color: #effcff;
  font-size: 14px;
  line-height: 1.55;
}

.llm-columns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.llm-columns div {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 12px;
  border: 1px solid rgba(90, 203, 222, 0.12);
  border-radius: 6px;
  background: rgba(3, 10, 16, 0.36);
}

.llm-columns p {
  margin: 0;
  color: #a9bdc3;
  font-size: 13px;
  line-height: 1.55;
}

.intel-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  gap: 16px;
}

.event-list,
.agent-list {
  display: grid;
  gap: 10px;
}

.event-list {
  max-height: 520px;
  overflow: auto;
  padding-right: 4px;
}

.event-row,
.agent-row {
  border: 1px solid rgba(90, 203, 222, 0.12);
  border-radius: 6px;
  background: rgba(3, 10, 16, 0.42);
}

.event-row {
  display: grid;
  gap: 8px;
  padding: 12px;
  color: #dce7e9;
  text-decoration: none;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
}

.event-row:hover {
  transform: translateX(2px);
  border-color: rgba(130, 243, 255, 0.52);
  background: rgba(9, 23, 32, 0.76);
}

.event-meta,
.event-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: #78909a;
  font-size: 12px;
}

.event-row strong {
  color: #eefcff;
  font-size: 14px;
  line-height: 1.45;
}

.event-type,
.sentiment-tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 850;
}

.event-type.news {
  color: #031118;
  background: #82f3ff;
}

.event-type.announcement {
  color: #181003;
  background: #ffca5b;
}

.sentiment-tag.positive {
  color: #26040c;
  background: #ff7b96;
}

.sentiment-tag.negative {
  color: #031118;
  background: #82f3ff;
}

.sentiment-tag.neutral {
  color: #dce7e9;
  background: rgba(148, 174, 181, 0.18);
}

.signal-panel,
.backtest-panel {
  min-height: 100%;
}

.signal-card {
  min-height: 220px;
  display: grid;
  align-content: center;
  gap: 10px;
}

.signal-card span {
  color: #78909a;
  font-size: 13px;
  font-weight: 850;
}

.signal-card strong {
  font: 900 54px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.source-times {
  display: grid;
  gap: 8px;
  margin-top: 8px;
}

.source-times div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(90, 203, 222, 0.12);
}

.source-times strong {
  color: #dce7e9;
  font: 800 12px/1.2 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  text-align: right;
}

.agent-row {
  display: grid;
  grid-template-columns: minmax(150px, 190px) minmax(0, 1fr);
  gap: 12px;
  padding: 12px;
}

.agent-row span {
  display: block;
  color: #78909a;
  font-size: 12px;
  margin-bottom: 6px;
}

.agent-row strong {
  color: #effcff;
  font-size: 13px;
}

.backtest-number {
  min-height: 104px;
  display: grid;
  align-content: center;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(90, 203, 222, 0.12);
}

.backtest-number strong {
  margin-top: 6px;
  color: #82f3ff;
  font: 900 40px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

strong.positive,
b.positive {
  color: #ff6f8d;
}

strong.negative,
b.negative {
  color: #82f3ff;
}

.seed-panel pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: #a9bdc3;
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.loading-shell {
  min-height: 520px;
}

.skeleton-line,
.skeleton-chart {
  border-radius: 6px;
  background: linear-gradient(90deg, rgba(49, 201, 230, 0.07) 25%, rgba(130, 243, 255, 0.16) 50%, rgba(49, 201, 230, 0.07) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

.skeleton-line {
  height: 28px;
  margin-bottom: 16px;
}

.skeleton-line.wide {
  width: min(420px, 58%);
}

.skeleton-chart {
  height: 420px;
}

@keyframes shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

@keyframes pulseScan {
  0%, 100% {
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.14), 0 0 26px rgba(45, 212, 255, 0.16);
  }
  50% {
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 0 44px rgba(255, 202, 91, 0.24);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
    transition-duration: 0.001ms !important;
  }
}

@media (max-width: 1120px) {
  .command-bar {
    grid-template-columns: minmax(180px, 1fr) minmax(0, auto);
  }

  .market-status {
    display: none;
  }

  .terminal-grid {
    grid-template-columns: 1fr;
  }

  .side-console {
    display: grid;
    grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
    align-items: start;
  }
}

@media (max-width: 860px) {
  .stage-head,
  .scenario-strip,
  .llm-columns,
  .intel-grid,
  .side-console {
    grid-template-columns: 1fr;
  }

  .forecast-panel {
    min-height: 0;
  }
}

@media (max-width: 640px) {
  .entry-screen {
    padding: 18px;
    place-items: start center;
    padding-top: 42px;
  }

  .entry-card {
    padding: 18px;
  }

  .entry-options {
    grid-template-columns: 1fr;
  }

  .entry-copy h1 {
    font-size: 38px;
  }

  .command-bar {
    height: auto;
    min-height: 68px;
    grid-template-columns: 1fr;
    align-items: start;
    gap: 10px;
    padding: 12px;
  }

  .brand-button,
  .header-actions {
    width: 100%;
    justify-self: stretch;
  }

  .header-actions {
    justify-content: stretch;
  }

  .ghost-button,
  .github-link {
    flex: 1;
  }

  .terminal-grid {
    width: calc(100% - 20px);
    margin-top: 10px;
    gap: 10px;
  }

  .side-console,
  .workbench {
    gap: 10px;
  }

  .surface,
  .chart-shell,
  .scenario-card {
    padding: 12px;
  }

  h1 {
    font-size: 25px;
  }

  .asset-block p {
    font-size: 12px;
  }

  .forecast-stats,
  .metric-grid,
  .agent-row {
    grid-template-columns: 1fr;
  }

  .kline-chart {
    min-height: 300px;
  }

  .chart-stamp {
    position: static;
    margin-top: 8px;
  }
}
</style>
