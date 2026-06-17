<template>
  <div class="stock-page" :data-theme="theme">
    <section v-if="!report && !loading" class="entry-screen">
      <div class="entry-shell">
        <header class="entry-topbar">
          <div class="brand-lockup">
            <span class="brand-glyph">烛</span>
            <span>
              <strong>烛机 CandleMind</strong>
              <small>A 股日 K 预言终端</small>
            </span>
          </div>
          <div class="theme-toggle" aria-label="主题切换">
            <button type="button" :class="{ active: theme === 'light' }" @click="setTheme('light')">白昼</button>
            <button type="button" :class="{ active: theme === 'dark' }" @click="setTheme('dark')">暗黑</button>
          </div>
        </header>

        <form class="entry-hero" @submit.prevent="loadProphecy">
          <div class="entry-copy">
            <h1>输入代码<br />点燃预言</h1>
            <p>烛机拉取真实 A 股日 K、近期事件与模型裁决，在最后一根真实 K 线后生成未来路径。</p>
            <label class="entry-pill" for="entry-stock-symbol">
              <input
                id="entry-stock-symbol"
                v-model="form.symbol"
                list="entry-symbol-list"
                maxlength="6"
                inputmode="numeric"
                autocomplete="off"
                autofocus
                aria-label="股票代码"
              />
              <button type="submit">开始预言</button>
              <datalist id="entry-symbol-list">
                <option v-for="item in symbols" :key="item.symbol" :value="item.symbol">
                  {{ item.name }}
                </option>
              </datalist>
            </label>
            <div class="entry-signals">
              <span>东方财富行情</span>
              <span>新闻公告事件</span>
              <span>{{ llmProviderLabel }} 模型裁决</span>
            </div>
            <div class="llm-config-card">
              <div>
                <span>当前模型</span>
                <strong>{{ llmModelLabel }}</strong>
                <small>{{ llmConfig?.baseUrl || '等待配置读取' }}</small>
              </div>
              <button type="button" @click="checkCurrentLlm" :disabled="checkingLlm">
                {{ checkingLlm ? '检测中' : '检测模型' }}
              </button>
              <p v-if="llmCheck" :class="llmCheck.ok ? 'ok' : 'failed'">
                {{ llmCheck.message }}
                <template v-if="llmCheck.latencyMs">({{ llmCheck.latencyMs }}ms)</template>
              </p>
            </div>
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
            <div class="entry-switches">
              <label class="toggle-field entry-toggle">
                <input v-model="form.includeEvents" type="checkbox" />
                <span>拉取近期新闻和公告事件</span>
              </label>
              <label class="toggle-field entry-toggle">
                <input v-model="form.useLlm" type="checkbox" />
                <span>启用当前模型裁决和预言</span>
              </label>
            </div>
            <p v-if="error" class="entry-error">{{ error }}</p>
          </div>

          <aside class="prophecy-instrument">
            <div class="instrument-head">
              <div>
                <span>SH 600519 / 1D</span>
                <strong>贵州茅台 烛机推演</strong>
              </div>
              <b>看多 67%</b>
            </div>
            <div class="preview-chart">
              <svg viewBox="0 0 520 310" preserveAspectRatio="none" aria-hidden="true">
                <path d="M24 195 C86 124 132 171 184 132 S286 100 330 145 S418 210 496 116" />
                <path class="forecast-preview-line" d="M360 158 C402 128 440 134 500 102" />
              </svg>
              <i class="preview-candle gain" style="--x:9%;--b:36%;--h:66px"></i>
              <i class="preview-candle risk" style="--x:17%;--b:45%;--h:48px"></i>
              <i class="preview-candle gain" style="--x:26%;--b:40%;--h:84px"></i>
              <i class="preview-candle gain" style="--x:36%;--b:50%;--h:58px"></i>
              <i class="preview-candle risk" style="--x:47%;--b:38%;--h:78px"></i>
              <i class="preview-candle gain" style="--x:58%;--b:48%;--h:88px"></i>
              <i class="preview-candle prophecy" style="--x:73%;--b:53%;--h:76px"></i>
              <i class="preview-candle prophecy" style="--x:84%;--b:60%;--h:62px"></i>
            </div>
            <div class="instrument-steps">
              <div><span></span><strong>连接行情与实时 K 线</strong><b>01</b></div>
              <div><span></span><strong>整理新闻公告事件</strong><b>02</b></div>
              <div><span></span><strong>请求当前模型主方向裁决</strong><b>03</b></div>
              <div><span></span><strong>生成单一路径预言 K 线</strong><b>04</b></div>
            </div>
          </aside>
        </form>
      </div>
    </section>

    <section v-else-if="loading" class="entry-screen loading-screen">
      <div class="entry-shell loading-shell">
        <header class="entry-topbar">
          <div class="brand-lockup">
            <span class="brand-glyph scanning">烛</span>
            <span>
              <strong>烛机 CandleMind</strong>
              <small>A 股日 K 预言终端</small>
            </span>
          </div>
          <div class="theme-toggle" aria-label="主题切换">
            <button type="button" :class="{ active: theme === 'light' }" @click="setTheme('light')">白昼</button>
            <button type="button" :class="{ active: theme === 'dark' }" @click="setTheme('dark')">暗黑</button>
          </div>
        </header>
        <div class="loading-hero">
          <div class="entry-copy">
            <h1>烛机正在推演</h1>
            <p>{{ form.symbol }} 的行情、事件和模型裁决正在汇合，完成后会一次性渲染完整结果。</p>
          </div>
          <div class="prophecy-instrument loading-instrument">
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
        <div class="theme-toggle compact" aria-label="主题切换">
          <button type="button" :class="{ active: theme === 'light' }" @click="setTheme('light')">白昼</button>
          <button type="button" :class="{ active: theme === 'dark' }" @click="setTheme('dark')">暗黑</button>
        </div>
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
            <span>启用当前模型裁决和预言</span>
          </label>
          <div class="side-llm-status">
            <span>模型</span>
            <strong>{{ llmProviderLabel }} / {{ llmModelLabel }}</strong>
            <button type="button" @click="checkCurrentLlm" :disabled="checkingLlm">
              {{ checkingLlm ? '检测中' : '检测模型' }}
            </button>
            <small v-if="llmCheck" :class="llmCheck.ok ? 'ok' : 'failed'">{{ llmCheck.message }}</small>
          </div>
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
            <div class="panel-title">当前模型裁决层</div>
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
import { checkLlmConfig, getLlmConfig } from '../api/config'
import { generateStockProphecy, searchStockSymbols } from '../api/stock'

const router = useRouter()
const loading = ref(false)
const loadingStepIndex = ref(0)
let loadingTimer = null
const error = ref('')
const report = ref(null)
const symbols = ref([])
const theme = ref(localStorage.getItem('candlemind-theme') || 'dark')
const llmConfig = ref(null)
const llmCheck = ref(null)
const checkingLlm = ref(false)
const loadingSteps = [
  '连接东方财富并拉取近期日K',
  '计算均线、RSI、ATR和相似形态',
  '抓取近期新闻和公告事件',
  '整理种子报告并请求当前模型',
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

const loadLlmConfig = async () => {
  try {
    const res = await getLlmConfig()
    llmConfig.value = res.data
  } catch (err) {
    llmConfig.value = null
  }
}

const checkCurrentLlm = async () => {
  checkingLlm.value = true
  llmCheck.value = null
  try {
    const res = await checkLlmConfig()
    llmCheck.value = res.data
    llmConfig.value = {
      configured: res.data.configured,
      baseUrl: res.data.baseUrl,
      model: res.data.model,
      supportsJsonMode: res.data.supportsJsonMode,
      apiKeySet: res.data.apiKeySet,
      apiKeyLooksPlaceholder: res.data.apiKeyLooksPlaceholder
    }
  } catch (err) {
    llmCheck.value = { ok: false, message: err.message || '模型检测失败' }
  } finally {
    checkingLlm.value = false
  }
}

const setTheme = (value) => {
  theme.value = value
  localStorage.setItem('candlemind-theme', value)
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

const llmModelLabel = computed(() => {
  if (!llmConfig.value) return '读取模型配置中'
  if (!llmConfig.value.configured) return '未配置真实模型'
  return llmConfig.value.model || '自定义模型'
})

const llmProviderLabel = computed(() => {
  const baseUrl = llmConfig.value?.baseUrl || ''
  if (!baseUrl) return 'OpenAI-compatible'
  if (baseUrl.includes('deepseek')) return 'DeepSeek'
  if (baseUrl.includes('dashscope') || baseUrl.includes('aliyun')) return '通义千问'
  if (baseUrl.includes('localhost:11434') || baseUrl.includes('ollama')) return 'Ollama'
  if (baseUrl.includes('localhost:1234')) return 'LM Studio'
  if (baseUrl.includes('openai.com')) return 'OpenAI'
  return 'OpenAI-compatible'
})

onMounted(() => {
  loadSymbols()
  loadLlmConfig()
})

onBeforeUnmount(() => {
  stopLoadingSteps()
})
</script>

<style scoped>
.stock-page {
  --bg: #05090b;
  --bg-2: #0b1417;
  --text: #edf7f7;
  --muted: #90a6aa;
  --soft: rgba(237, 247, 247, 0.06);
  --line: rgba(255, 90, 102, 0.2);
  --panel: rgba(8, 18, 22, 0.78);
  --panel-solid: #0b1519;
  --accent: #ff5a66;
  --accent-deep: #b5232e;
  --accent-2: #e0b45a;
  --accent-ink: #051014;
  --risk: #8ba3aa;
  --risk-soft: rgba(139, 163, 170, 0.18);
  --shadow: rgba(0, 0, 0, 0.42);
  --chart-grid: rgba(255, 90, 102, 0.11);
  --forecast: rgba(224, 180, 90, 0.12);
  min-height: 100dvh;
  color: var(--text);
  background:
    radial-gradient(circle at 50% 45%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 34%),
    radial-gradient(circle at 76% 16%, color-mix(in srgb, var(--accent-2) 14%, transparent), transparent 30%),
    linear-gradient(180deg, var(--bg), var(--bg-2));
  font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  overflow-x: hidden;
}

.stock-page[data-theme="light"] {
  --bg: #f3f7f8;
  --bg-2: #e8eef1;
  --text: #10191d;
  --muted: #617177;
  --soft: rgba(16, 25, 29, 0.06);
  --line: rgba(181, 35, 46, 0.16);
  --panel: rgba(255, 255, 255, 0.74);
  --panel-solid: #ffffff;
  --accent: #b5232e;
  --accent-deep: #8f1b25;
  --accent-2: #c8953d;
  --accent-ink: #f8fbfb;
  --risk: #52636b;
  --risk-soft: rgba(82, 99, 107, 0.12);
  --shadow: rgba(28, 47, 57, 0.16);
  --chart-grid: rgba(181, 35, 46, 0.11);
  --forecast: rgba(200, 149, 61, 0.13);
}

.stock-page::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, var(--chart-grid) 1px, transparent 1px),
    linear-gradient(0deg, var(--chart-grid) 1px, transparent 1px);
  background-size: 54px 54px;
  mask-image: radial-gradient(circle at center, black, transparent 72%);
  opacity: 0.6;
  z-index: 0;
}

.stock-page::after {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(255,255,255,0.035) 50%, rgba(0,0,0,0.025) 50%);
  background-size: 100% 5px;
  opacity: 0.12;
  z-index: 1;
}

.command-bar,
.terminal-grid,
.entry-screen {
  position: relative;
  z-index: 2;
}

.entry-screen {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 0 16px;
}

.entry-shell {
  width: min(1180px, 100%);
  min-height: 100dvh;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
}

.entry-topbar {
  height: 76px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.brand-lockup,
.brand-button {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-glyph,
.brand-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  color: var(--accent-ink);
  background: var(--accent);
  font: 950 20px/1 "Songti SC", serif;
  box-shadow: 0 18px 38px color-mix(in srgb, var(--accent) 24%, transparent);
}

.brand-mark img {
  width: 30px;
  height: 30px;
  display: block;
  filter: saturate(0.9) hue-rotate(120deg);
}

.brand-lockup strong,
.brand-copy strong {
  display: block;
  color: var(--text);
  font-size: 15px;
  line-height: 1.1;
}

.brand-lockup small,
.brand-copy small {
  display: block;
  margin-top: 3px;
  color: var(--muted);
  font: 800 11px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.theme-toggle {
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--panel);
  box-shadow: 0 18px 50px var(--shadow);
  backdrop-filter: blur(16px);
}

.theme-toggle.compact {
  box-shadow: none;
}

.theme-toggle button {
  height: 34px;
  min-width: 72px;
  border: 0;
  border-radius: 999px;
  color: var(--muted);
  background: transparent;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.theme-toggle button.active {
  color: var(--accent-ink);
  background: var(--accent);
}

.entry-hero,
.loading-hero {
  min-height: calc(100dvh - 76px);
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: 42px;
  align-items: center;
  padding: 24px 0 44px;
}

.entry-copy {
  display: grid;
  gap: 22px;
  align-content: center;
}

.entry-copy h1,
h1 {
  margin: 0;
  color: var(--text);
  letter-spacing: 0;
}

.entry-copy h1 {
  max-width: 640px;
  font-size: clamp(54px, 8vw, 92px);
  line-height: 0.95;
}

.entry-copy p {
  max-width: 520px;
  margin: 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.75;
}

.entry-pill {
  width: min(540px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  padding: 8px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--panel);
  box-shadow: 0 24px 70px var(--shadow), inset 0 1px 0 rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(18px);
}

.entry-pill input {
  min-width: 0;
  height: 50px;
  border: 0;
  padding: 0 18px;
  color: var(--text);
  background: transparent;
  outline: none;
  font: 950 28px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  letter-spacing: 0.08em;
}

.entry-pill button,
.primary-button {
  border: 0;
  color: var(--accent-ink);
  background: var(--accent);
  font-weight: 950;
  cursor: pointer;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.28), 0 16px 34px color-mix(in srgb, var(--accent) 22%, transparent);
}

.entry-pill button {
  height: 50px;
  min-width: 126px;
  border-radius: 999px;
}

.entry-signals {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: var(--muted);
  font: 850 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.entry-signals span {
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--soft);
}

.llm-config-card,
.side-llm-status {
  width: min(540px, 100%);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--soft);
}

.llm-config-card span,
.side-llm-status span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  font-weight: 850;
}

.llm-config-card strong,
.side-llm-status strong {
  display: block;
  margin-top: 5px;
  color: var(--text);
  font-size: 14px;
  line-height: 1.25;
}

.llm-config-card small,
.side-llm-status small {
  display: block;
  margin-top: 5px;
  color: var(--muted);
  font: 800 11px/1.35 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  overflow-wrap: anywhere;
}

.llm-config-card button,
.side-llm-status button {
  height: 36px;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 0 13px;
  color: var(--text);
  background: var(--panel);
  font-size: 12px;
  font-weight: 900;
  cursor: pointer;
}

.llm-config-card p {
  grid-column: 1 / -1;
  margin: 0;
  font-size: 12px;
  line-height: 1.45;
}

.llm-config-card .ok,
.side-llm-status .ok {
  color: var(--accent);
}

.llm-config-card .failed,
.side-llm-status .failed {
  color: var(--risk);
}

.entry-options {
  width: min(540px, 100%);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.entry-switches {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
}

.prophecy-instrument {
  position: relative;
  min-height: 530px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 28px;
  background: var(--panel);
  box-shadow: 0 34px 90px var(--shadow), inset 0 1px 0 rgba(255, 255, 255, 0.24);
  backdrop-filter: blur(22px);
}

.prophecy-instrument::before {
  content: '';
  position: absolute;
  inset: -44px;
  z-index: -1;
  border: 1px solid color-mix(in srgb, var(--accent) 20%, transparent);
  border-radius: 50%;
  transform: rotate(-10deg);
}

.instrument-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 14px;
}

.instrument-head span {
  display: block;
  margin-bottom: 5px;
  color: var(--muted);
  font: 850 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.instrument-head strong {
  color: var(--text);
  font-size: 20px;
  line-height: 1.1;
}

.instrument-head b {
  padding: 11px 13px;
  border: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  border-radius: 16px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  font: 950 18px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.preview-chart {
  height: 310px;
  position: relative;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 22px;
  background:
    linear-gradient(0deg, var(--chart-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--chart-grid) 1px, transparent 1px),
    color-mix(in srgb, var(--panel-solid) 84%, transparent);
  background-size: 100% 52px, 52px 100%, auto;
}

.preview-chart::before {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 29%;
  background: var(--forecast);
  border-left: 1px dashed color-mix(in srgb, var(--accent-2) 65%, transparent);
}

.preview-chart svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.preview-chart path {
  fill: none;
  stroke: var(--accent);
  stroke-width: 2.4;
  opacity: 0.72;
}

.preview-chart .forecast-preview-line {
  stroke: var(--accent-2);
  stroke-width: 2.8;
  opacity: 0.88;
}

.preview-candle {
  position: absolute;
  left: var(--x);
  bottom: var(--b);
  width: 9px;
  height: var(--h);
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 -24px 0 -3px var(--accent), 0 24px 0 -3px var(--accent);
}

.preview-candle.risk {
  background: var(--risk);
  box-shadow: 0 -24px 0 -3px var(--risk), 0 24px 0 -3px var(--risk);
}

.preview-candle.prophecy {
  width: 10px;
  background: var(--accent-2);
  box-shadow: 0 -28px 0 -3px var(--accent-2), 0 26px 0 -3px var(--accent-2);
}

.instrument-steps,
.loading-stack {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.instrument-steps div,
.loading-step {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-height: 42px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--soft);
}

.instrument-steps span,
.step-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid color-mix(in srgb, var(--accent) 22%, transparent);
  border-top-color: var(--accent);
  border-radius: 50%;
}

.instrument-steps strong,
.loading-step strong {
  color: var(--text);
  font-size: 13px;
  line-height: 1.35;
}

.instrument-steps b {
  color: var(--muted);
  font: 850 11px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.loading-shell {
  width: min(1180px, 100%);
}

.loading-instrument {
  min-height: 360px;
}

.step-indicator {
  width: 24px;
  height: 24px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  border: 1px solid var(--line);
  font: 850 11px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.step-indicator b {
  font: inherit;
}

.loading-step {
  grid-template-columns: 30px minmax(0, 1fr);
  color: var(--muted);
}

.loading-step.done .step-indicator {
  color: var(--accent-ink);
  background: var(--accent);
}

.loading-step.active {
  border-color: color-mix(in srgb, var(--accent-2) 48%, transparent);
  box-shadow: inset 3px 0 0 var(--accent-2);
}

.loading-step.active .step-indicator {
  color: var(--accent-ink);
  background: var(--accent-2);
}

.step-spinner {
  width: 13px;
  height: 13px;
  animation: spin 0.78s linear infinite;
}

.entry-error,
.error-strip {
  margin: 0;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--accent) 62%, transparent);
  border-radius: 10px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  color: var(--accent);
  font-size: 13px;
  font-weight: 750;
}

.command-bar {
  min-height: 72px;
  display: grid;
  grid-template-columns: minmax(190px, 1fr) auto minmax(250px, 1fr);
  align-items: center;
  gap: 16px;
  padding: 10px 22px;
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--panel-solid) 86%, transparent);
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 5;
  box-shadow: 0 18px 50px var(--shadow);
}

.brand-button {
  justify-self: start;
  border: 0;
  background: transparent;
  color: var(--text);
  cursor: pointer;
  min-width: 0;
}

.market-status {
  justify-self: center;
  display: grid;
  grid-template-columns: repeat(3, auto);
  align-items: center;
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--panel);
}

.market-status span {
  min-width: 72px;
  height: 32px;
  display: grid;
  place-items: center;
  padding: 0 10px;
  color: var(--muted);
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
.primary-button {
  height: 38px;
  border-radius: 999px;
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

.ghost-button {
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--text);
}

.ghost-button:hover {
  border-color: color-mix(in srgb, var(--accent) 56%, transparent);
  background: var(--soft);
}

.primary-button {
  width: 100%;
}

.primary-button:active,
.ghost-button:active,
.entry-pill button:active {
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
  border: 1px solid var(--line);
  border-radius: 18px;
  background: var(--panel);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 18px 45px var(--shadow);
  backdrop-filter: blur(16px);
}

.surface::before,
.scenario-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 52%, transparent), transparent);
  opacity: 0.7;
  pointer-events: none;
}

.surface {
  padding: 16px;
}

.panel-title {
  margin-bottom: 14px;
  color: var(--accent);
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
  color: var(--muted);
  font-size: 12px;
  font-weight: 750;
}

input,
select {
  width: 100%;
  height: 42px;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0 11px;
  color: var(--text);
  background: color-mix(in srgb, var(--panel-solid) 74%, transparent);
  font-family: inherit;
  outline: none;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,0.02);
}

input:focus,
select:focus {
  border-color: color-mix(in srgb, var(--accent) 78%, transparent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent) 14%, transparent);
}

select option {
  background: var(--panel-solid);
  color: var(--text);
}

.toggle-field {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 6px 0 16px;
  color: var(--text);
  font-size: 13px;
  font-weight: 750;
}

.toggle-field input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.entry-toggle {
  margin: 0;
}

.micro-copy {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
}

.side-llm-status {
  width: 100%;
  grid-template-columns: 1fr;
  margin-top: 12px;
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
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--soft);
}

.metric-grid strong {
  color: var(--text);
  font: 850 18px/1.05 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-word;
}

.provider-cell {
  grid-column: 1 / -1;
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
  color: var(--muted);
  font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.asset-line strong {
  color: var(--text);
  font-size: 14px;
}

h1 {
  font-size: clamp(24px, 3vw, 38px);
  line-height: 1.05;
}

.asset-block p {
  max-width: 68ch;
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.forecast-panel {
  display: grid;
  gap: 12px;
  min-height: 122px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid var(--line);
  background: var(--soft);
}

.forecast-panel strong {
  color: var(--text);
  font-size: 26px;
  line-height: 1;
}

.forecast-panel.tone-bull {
  border-color: color-mix(in srgb, var(--accent) 44%, transparent);
  box-shadow: inset 3px 0 0 var(--accent);
}

.forecast-panel.tone-bear {
  border-color: color-mix(in srgb, var(--risk) 46%, transparent);
  box-shadow: inset 3px 0 0 var(--risk);
}

.forecast-panel.tone-neutral {
  border-color: color-mix(in srgb, var(--accent-2) 42%, transparent);
  box-shadow: inset 3px 0 0 var(--accent-2);
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
  border-top: 1px solid var(--line);
}

.forecast-stats b {
  color: var(--text);
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
  border: 1px solid var(--line);
  border-radius: 18px;
  background:
    linear-gradient(90deg, var(--chart-grid) 1px, transparent 1px),
    linear-gradient(0deg, var(--chart-grid) 1px, transparent 1px),
    color-mix(in srgb, var(--panel-solid) 88%, transparent);
  background-size: 52px 52px, 52px 52px, auto;
  box-shadow: inset 0 0 44px color-mix(in srgb, var(--accent) 5%, transparent);
}

.chart-stamp {
  position: absolute;
  right: 12px;
  top: 12px;
  display: grid;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: var(--panel);
  backdrop-filter: blur(10px);
}

.chart-stamp span {
  color: var(--muted);
  font-size: 11px;
}

.chart-stamp strong {
  color: var(--text);
  font: 800 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.grid line {
  stroke: color-mix(in srgb, var(--muted) 28%, transparent);
}

.axis-label,
.forecast-label {
  fill: var(--muted);
  font-size: 11px;
  font-weight: 800;
}

.forecast-label {
  fill: var(--accent-2);
}

.up,
.up-fill,
.forecast-up,
.forecast-up-fill {
  stroke: var(--accent);
}

.up-fill,
.forecast-up-fill {
  fill: var(--accent);
}

.down,
.down-fill,
.forecast-down,
.forecast-down-fill {
  stroke: var(--risk);
}

.down-fill,
.forecast-down-fill {
  fill: var(--risk);
}

.forecast-band {
  fill: var(--forecast);
}

.forecast-divider {
  stroke: color-mix(in srgb, var(--accent-2) 86%, transparent);
  stroke-width: 1.4;
  stroke-dasharray: 5 5;
}

.forecast-up,
.forecast-down {
  stroke-width: 2;
}

.forecast-up-fill,
.forecast-down-fill {
  stroke-width: 1;
  opacity: 0.9;
}

.ma-line,
.level {
  fill: none;
  stroke-width: 1.8;
}

.ma5 {
  stroke: var(--accent-2);
}

.ma20 {
  stroke: color-mix(in srgb, var(--risk) 82%, var(--text));
}

.support,
.resistance {
  stroke: color-mix(in srgb, var(--text) 46%, transparent);
  stroke-width: 1;
  stroke-dasharray: 3 5;
}

.legend-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 11px;
  color: var(--muted);
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
  background: var(--accent);
}

.down-dot {
  background: var(--risk);
}

.ma5-dot,
.prophecy-dot {
  background: var(--accent-2);
}

.ma20-dot {
  background: var(--risk);
}

.prophecy-dot {
  box-shadow: 0 0 12px color-mix(in srgb, var(--accent-2) 42%, transparent);
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
  border-color: color-mix(in srgb, var(--accent-2) 58%, transparent);
  background: color-mix(in srgb, var(--panel-solid) 76%, transparent);
}

.scenario-card.tone-bull.active {
  box-shadow: inset 3px 0 0 var(--accent), 0 18px 45px var(--shadow);
}

.scenario-card.tone-bear.active {
  box-shadow: inset 3px 0 0 var(--risk), 0 18px 45px var(--shadow);
}

.scenario-card.tone-neutral.active {
  box-shadow: inset 3px 0 0 var(--accent-2), 0 18px 45px var(--shadow);
}

.scenario-top {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 10px;
  color: var(--text);
  font-size: 13px;
  font-weight: 850;
}

.scenario-top strong {
  color: var(--text);
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
  background: var(--accent-2);
}

.scenario-card.tone-bull .probability-bar span {
  background: var(--accent);
}

.scenario-card.tone-bear .probability-bar span {
  background: var(--risk);
}

.scenario-card.tone-neutral .probability-bar span {
  background: var(--accent-2);
}

.scenario-card p,
.agent-row p,
.event-row p,
.signal-card p,
.empty-copy,
.llm-columns p,
.seed-panel pre {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.55;
}

.scenario-card small {
  display: block;
  margin-top: 10px;
  color: var(--muted);
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
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--soft);
}

.llm-status.ok {
  border-color: color-mix(in srgb, var(--accent) 34%, transparent);
  box-shadow: inset 3px 0 0 var(--accent);
}

.llm-status.fallback {
  border-color: color-mix(in srgb, var(--accent-2) 34%, transparent);
  box-shadow: inset 3px 0 0 var(--accent-2);
}

.llm-status span,
.llm-columns span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 850;
}

.llm-status strong {
  color: var(--text);
  font-size: 14px;
  line-height: 1.55;
}

.llm-columns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.llm-columns div,
.event-row,
.agent-row {
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--soft);
}

.llm-columns div {
  min-width: 0;
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 12px;
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

.event-row {
  display: grid;
  gap: 8px;
  padding: 12px;
  color: var(--text);
  text-decoration: none;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease;
}

.event-row:hover {
  transform: translateX(2px);
  border-color: color-mix(in srgb, var(--accent) 52%, transparent);
  background: color-mix(in srgb, var(--panel-solid) 72%, transparent);
}

.event-meta,
.event-tags {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 12px;
}

.event-row strong {
  color: var(--text);
  font-size: 14px;
  line-height: 1.45;
}

.event-type,
.sentiment-tag {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 850;
}

.event-type.news,
.sentiment-tag.positive {
  color: var(--accent-ink);
  background: var(--accent);
}

.event-type.announcement {
  color: var(--accent-ink);
  background: var(--accent-2);
}

.sentiment-tag.negative {
  color: var(--text);
  background: var(--risk-soft);
}

.sentiment-tag.neutral {
  color: var(--text);
  background: var(--soft);
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
  color: var(--muted);
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
  border-top: 1px solid var(--line);
}

.source-times strong {
  color: var(--text);
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
  color: var(--muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.agent-row strong {
  color: var(--text);
  font-size: 13px;
}

.backtest-number {
  min-height: 104px;
  display: grid;
  align-content: center;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

.backtest-number strong {
  margin-top: 6px;
  color: var(--accent);
  font: 900 40px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

strong.positive,
b.positive {
  color: var(--accent);
}

strong.negative,
b.negative {
  color: var(--risk);
}

.seed-panel pre {
  white-space: pre-wrap;
  word-break: break-word;
  font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.loading-shell .skeleton-line,
.loading-shell .skeleton-chart,
.skeleton-line,
.skeleton-chart {
  border-radius: 14px;
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 7%, transparent) 25%, color-mix(in srgb, var(--accent) 16%, transparent) 50%, color-mix(in srgb, var(--accent) 7%, transparent) 75%);
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
  0%, 100% { box-shadow: 0 18px 38px color-mix(in srgb, var(--accent) 22%, transparent); }
  50% { box-shadow: 0 18px 58px color-mix(in srgb, var(--accent-2) 32%, transparent); }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.scanning {
  animation: pulseScan 1.8s ease-in-out infinite;
}

@media (prefers-reduced-motion: no-preference) {
  .brand-glyph,
  .prophecy-instrument {
    animation: rise 700ms cubic-bezier(0.16, 1, 0.3, 1) both;
  }

  .instrument-steps span {
    animation: spin 900ms linear infinite;
  }
}

@keyframes rise {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: translateY(0); }
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

@media (max-width: 900px) {
  .entry-topbar {
    height: auto;
    padding: 18px 0;
  }

  .entry-hero,
  .loading-hero {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .entry-copy h1 {
    font-size: clamp(48px, 15vw, 72px);
  }

  .entry-pill {
    grid-template-columns: 1fr;
    border-radius: 24px;
  }

  .entry-pill button {
    width: 100%;
  }

  .prophecy-instrument {
    min-height: auto;
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
    padding: 0 14px;
    place-items: start center;
  }

  .entry-shell {
    min-height: auto;
  }

  .entry-topbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .entry-options {
    grid-template-columns: 1fr;
  }

  .theme-toggle,
  .theme-toggle.compact {
    width: 100%;
  }

  .theme-toggle button {
    width: 100%;
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
    flex-wrap: wrap;
  }

  .ghost-button {
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
