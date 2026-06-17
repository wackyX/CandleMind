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
	            <div class="mode-switch" aria-label="推演模式">
	              <button type="button" :class="{ active: form.mode === 'live' }" @click="form.mode = 'live'">实时预言</button>
	              <button type="button" :class="{ active: form.mode === 'backtest' }" @click="form.mode = 'backtest'">历史回测</button>
	            </div>
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
	              <button type="submit">{{ form.mode === 'backtest' ? '开始回测' : '开始预言' }}</button>
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
	              <label v-if="form.mode === 'backtest'" class="field" for="entry-backtest-date">
	                <span>回测日期</span>
	                <input id="entry-backtest-date" v-model="form.asOfDate" type="date" />
	              </label>
	            </div>
	            <div class="entry-switches">
	              <label v-if="form.mode === 'live'" class="toggle-field entry-toggle">
	                <input v-model="form.includeEvents" type="checkbox" />
	                <span>拉取近期新闻和公告事件</span>
	              </label>
	              <label v-if="form.mode === 'live'" class="toggle-field entry-toggle">
	                <input v-model="form.useLlm" type="checkbox" />
	                <span>启用当前模型裁决和预言</span>
	              </label>
	              <label v-else class="toggle-field entry-toggle">
	                <input v-model="form.useBacktestLlm" type="checkbox" />
	                <span>回测时启用当前模型</span>
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
            <div class="live-kline-loader">
              <div class="loader-head">
                <span>逐日回放</span>
                <strong>{{ loadingSteps[loadingStepIndex] }}</strong>
              </div>
              <div class="loader-chart" aria-hidden="true">
                <i
                  v-for="(item, index) in loadingCandles"
                  :key="`loader-candle-${index}`"
                  :class="['loader-candle', item.tone]"
                  :style="{
                    '--x': item.x,
                    '--b': item.b,
                    '--h': item.h,
                    '--d': `${index * 0.13}s`
                  }"
                ></i>
                <span class="scan-beam"></span>
              </div>
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
	          <div class="mode-switch compact" aria-label="推演模式">
	            <button type="button" :class="{ active: form.mode === 'live' }" @click="form.mode = 'live'">实时</button>
	            <button type="button" :class="{ active: form.mode === 'backtest' }" @click="form.mode = 'backtest'">回测</button>
	          </div>
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
	          <label v-if="form.mode === 'backtest'" class="field" for="stock-backtest-date">
	            <span>回测日期</span>
	            <input id="stock-backtest-date" v-model="form.asOfDate" type="date" />
	          </label>
	          <label v-if="form.mode === 'live'" class="toggle-field">
	            <input v-model="form.includeEvents" type="checkbox" />
	            <span>拉取近期新闻和公告事件</span>
	          </label>
	          <label v-if="form.mode === 'live'" class="toggle-field">
	            <input v-model="form.useLlm" type="checkbox" />
	            <span>启用当前模型裁决和预言</span>
	          </label>
	          <label v-else class="toggle-field">
	            <input v-model="form.useBacktestLlm" type="checkbox" />
	            <span>回测时启用当前模型</span>
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
	            {{ loading ? '正在生成' : form.mode === 'backtest' ? '运行回测' : '生成预言' }}
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
	                <p>{{ report.mode === 'backtest' ? `以 ${report.backtest?.asOfDate} 为历史切点，生成当时可见数据下的预言，并对比之后真实走势。` : `未来 ${report.horizon} 个交易日，基于真实日K、近期新闻公告和相似形态生成单一路径。` }}</p>
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

            <div class="chart-analysis-layout">
              <div class="chart-main-column">
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
                  <line :x1="item.x" :x2="item.x" :y1="item.highY" :y2="item.lowY" :class="item.up ? 'up' : 'down'" :style="{ '--d': `${item.animationIndex * 0.014}s` }" />
                  <rect
                    :x="item.x - item.width / 2"
                    :y="Math.min(item.openY, item.closeY)"
                    :width="item.width"
                    :height="Math.max(1, Math.abs(item.closeY - item.openY))"
                    :class="item.up ? 'up-fill' : 'down-fill'"
                    :style="{ '--d': `${item.animationIndex * 0.014}s` }"
                  />
                </g>
              </g>
	              <g class="forecast-candles">
                <g
                  v-for="item in chart.forecastCandles"
                  :key="`forecast-${item.day}`"
                  :class="[
                    'prophecy-candle',
                    item.up ? 'is-up' : 'is-down',
                    item.wickMode,
                    { active: selectedForecastIndex === item.animationIndex }
                  ]"
                  role="button"
                  tabindex="0"
                  :aria-label="`查看第${item.day}个交易日预言解释`"
                  :style="{ '--d': `${2 + item.animationIndex * 0.78}s`, '--body-shift': `${item.bodyShift}px` }"
                  @mouseenter="selectedForecastIndex = item.animationIndex"
                  @focus="selectedForecastIndex = item.animationIndex"
                  @click="selectedForecastIndex = item.animationIndex"
                  @keydown.enter.prevent="selectedForecastIndex = item.animationIndex"
                  @keydown.space.prevent="selectedForecastIndex = item.animationIndex"
                >
                  <line
                    class="forecast-wick upper-wick"
                    :x1="item.x"
                    :x2="item.x"
                    :y1="item.highY"
                    :y2="item.bodyTopY"
                  />
                  <line
                    class="forecast-wick lower-wick"
                    :x1="item.x"
                    :x2="item.x"
                    :y1="item.bodyBottomY"
                    :y2="item.lowY"
                  />
                  <rect
                    class="forecast-body"
                    :x="item.x - item.width / 2"
                    :y="item.bodyTopY"
                    :width="item.width"
                    :height="item.bodyHeight"
                  />
                  <circle
                    v-if="item.wickMode === 'upper-first' && item.upperWickHeight > 2"
                    class="wick-flash upper-flash"
                    :cx="item.x"
                    :cy="item.highY"
                    r="3.5"
                  />
                  <circle
                    v-if="item.wickMode === 'lower-first' && item.lowerWickHeight > 2"
                    class="wick-flash lower-flash"
                    :cx="item.x"
                    :cy="item.lowY"
                    r="3.5"
                  />
	              </g>
	              <g v-if="chart.actualCandles.length" class="actual-candles">
	                <g v-for="item in chart.actualCandles" :key="`actual-${item.date}`">
	                  <line :x1="item.x" :x2="item.x" :y1="item.highY" :y2="item.lowY" />
	                  <rect
	                    :x="item.x - item.width / 2"
	                    :y="item.bodyTopY"
	                    :width="item.width"
	                    :height="item.bodyHeight"
	                  />
	                </g>
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
	                  <span v-if="report.backtest"><i class="dot actual-dot"></i>回测真实K线</span>
	                </div>
              </div>

              <aside v-if="credibilityBreakdown" class="credibility-radar-panel">
                <div class="radar-head">
                  <div>
                    <span>可信度雷达</span>
                    <strong>{{ credibilityBreakdown.score }}</strong>
                  </div>
                  <b>{{ credibilityBreakdown.label }}</b>
                </div>
                <svg class="credibility-radar" viewBox="0 0 240 240" role="img" aria-label="预言可信度雷达图">
                  <polygon
                    v-for="points in credibilityBreakdown.radarGrid"
                    :key="`grid-${points}`"
                    class="radar-grid-shape"
                    :points="points"
                  />
                  <line
                    v-for="axis in credibilityBreakdown.radarAxes"
                    :key="`axis-${axis.key}`"
                    class="radar-axis"
                    x1="120"
                    y1="120"
                    :x2="axis.x"
                    :y2="axis.y"
                  />
                  <polygon class="radar-score-shape" :points="credibilityBreakdown.radarPolygon" />
                  <circle
                    v-for="point in credibilityBreakdown.radarPoints"
                    :key="`point-${point.key}`"
                    class="radar-point"
                    :cx="point.x"
                    :cy="point.y"
                    r="4"
                  />
                  <text
                    v-for="axis in credibilityBreakdown.radarAxes"
                    :key="`label-${axis.key}`"
                    class="radar-label"
                    :x="axis.labelX"
                    :y="axis.labelY"
                    text-anchor="middle"
                  >
                    {{ axis.shortName }}
                  </text>
                  <text class="radar-center-score" x="120" y="116" text-anchor="middle">{{ credibilityBreakdown.score }}</text>
                  <text class="radar-center-label" x="120" y="135" text-anchor="middle">综合</text>
                </svg>
                <div class="radar-legend-list">
                  <div v-for="item in credibilityBreakdown.items" :key="`radar-note-${item.key}`">
                    <span>{{ item.name }}</span>
                    <strong>{{ item.score }}</strong>
                    <p>{{ item.shortReason }}</p>
                  </div>
                </div>
              </aside>
	            </div>

	            <div v-if="backtestSummary" class="backtest-compare-panel">
	              <div class="compare-verdict">
	                <span>历史回测</span>
	                <strong :class="backtestSummary.directionHit ? 'positive' : 'negative'">
	                  {{ backtestSummary.directionHit ? '方向命中' : '方向偏离' }}
	                </strong>
	                <small>命中分 {{ backtestSummary.hitScore }}</small>
	              </div>
	              <div class="compare-metrics">
	                <div>
	                  <span>回测切点</span>
	                  <strong>{{ backtestSummary.baseDate }}</strong>
	                </div>
	                <div>
	                  <span>预言收益</span>
	                  <strong :class="signedClass(backtestSummary.predictedReturnPct)">{{ backtestSummary.predictedReturnPct }}%</strong>
	                </div>
	                <div>
	                  <span>真实收益</span>
	                  <strong :class="signedClass(backtestSummary.actualReturnPct)">{{ backtestSummary.actualReturnPct }}%</strong>
	                </div>
	                <div>
	                  <span>平均偏差</span>
	                  <strong>{{ backtestSummary.avgAbsErrorPct }}%</strong>
	                </div>
	              </div>
	            </div>

	            <div v-if="selectedForecastInsight" class="forecast-insight">
              <div class="insight-head">
                <span>第 {{ selectedForecastInsight.day }} 个交易日</span>
                <strong>{{ selectedForecastInsight.title }}</strong>
              </div>
              <p>{{ selectedForecastInsight.story }}</p>
              <div class="insight-metrics">
                <div>
                  <span>开</span>
                  <strong>{{ selectedForecastInsight.open }}</strong>
                </div>
                <div>
                  <span>高</span>
                  <strong>{{ selectedForecastInsight.high }}</strong>
                </div>
                <div>
                  <span>低</span>
                  <strong>{{ selectedForecastInsight.low }}</strong>
                </div>
                <div>
                  <span>收</span>
                  <strong :class="signedClass(selectedForecastInsight.changePct)">{{ selectedForecastInsight.close }}</strong>
                </div>
              </div>
              <div class="insight-notes">
                <span>{{ selectedForecastInsight.wickNote }}</span>
                <span>{{ selectedForecastInsight.rangeNote }}</span>
                <span>{{ selectedForecastInsight.invalidNote }}</span>
              </div>
              <div class="forecast-day-tabs" aria-label="预言交易日选择">
                <button
                  v-for="item in forecastInsights"
                  :key="`forecast-tab-${item.day}`"
                  type="button"
                  :class="{ active: selectedForecastIndex === item.index }"
                  @click="selectedForecastIndex = item.index"
                >
                  D{{ item.day }}
                </button>
              </div>
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
import { backtestStockProphecy, generateStockProphecy, searchStockSymbols } from '../api/stock'

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
const selectedForecastIndex = ref(0)
const loadingSteps = [
  '连接东方财富并拉取近期日K',
  '计算均线、RSI、ATR和相似形态',
  '抓取近期新闻和公告事件',
  '整理种子报告并请求当前模型',
  '生成单一路径预言K线',
  '校验风险边界并渲染结果'
]
const loadingCandles = [
  { x: '7%', b: '28%', h: '52px', tone: 'gain' },
  { x: '13%', b: '36%', h: '66px', tone: 'gain' },
  { x: '19%', b: '32%', h: '44px', tone: 'risk' },
  { x: '25%', b: '41%', h: '78px', tone: 'gain' },
  { x: '31%', b: '45%', h: '58px', tone: 'gain' },
  { x: '37%', b: '38%', h: '84px', tone: 'risk' },
  { x: '43%', b: '48%', h: '70px', tone: 'gain' },
  { x: '49%', b: '52%', h: '62px', tone: 'gain' },
  { x: '55%', b: '44%', h: '76px', tone: 'risk' },
  { x: '61%', b: '51%', h: '88px', tone: 'gain' },
  { x: '67%', b: '58%', h: '68px', tone: 'gain' },
  { x: '74%', b: '56%', h: '86px', tone: 'prophecy' },
  { x: '81%', b: '63%', h: '72px', tone: 'prophecy' },
  { x: '88%', b: '69%', h: '58px', tone: 'prophecy' }
]

function defaultBacktestDate() {
  const date = new Date()
  date.setDate(date.getDate() - 30)
  return date.toISOString().slice(0, 10)
}

const form = reactive({
  mode: 'live',
  symbol: '600519',
  horizon: 5,
  days: 180,
  asOfDate: defaultBacktestDate(),
  includeEvents: true,
  useLlm: true,
  useBacktestLlm: false
})

const chart = computed(() => {
	  if (!report.value) {
	    return { width: 980, height: 440, padding: { left: 56, right: 62, top: 26, bottom: 36 }, priceTicks: [], candles: [], forecastCandles: [], actualCandles: [], forecastBand: null }
	  }
  const width = 980
  const height = 440
  const padding = { left: 56, right: 62, top: 26, bottom: 36 }
	  const visibleCandles = report.value.candles.slice(-88)
	  const forecastSource = report.value.forecast?.candles || []
	  const actualSource = report.value.backtest?.actualCandles || []
	  const projectedValues = forecastSource.flatMap((item) => [item.high, item.low, item.open, item.close])
	  const actualValues = actualSource.flatMap((item) => [item.high, item.low, item.open, item.close])
	  const allPrices = visibleCandles.flatMap((item) => [item.high, item.low]).concat(projectedValues, actualValues)
  const minPrice = Math.min(...allPrices) * 0.985
  const maxPrice = Math.max(...allPrices) * 1.015
  const innerWidth = width - padding.left - padding.right
  const innerHeight = height - padding.top - padding.bottom
	  const totalSlots = visibleCandles.length + Math.max(report.value.paths.length, actualSource.length) + 2
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
    up: item.close >= item.open,
    animationIndex: index
  }))
	  const forecastCandles = []
  forecastSource.forEach((item, index) => {
    const openY = y(item.open)
    const closeY = y(item.close)
    const highY = y(item.high)
    const lowY = y(item.low)
    const bodyTopY = Math.min(openY, closeY)
    const bodyBottomY = Math.max(openY, closeY)
    const upperWickHeight = Math.max(0, bodyTopY - highY)
    const lowerWickHeight = Math.max(0, lowY - bodyBottomY)
    const wickMode = upperWickHeight >= lowerWickHeight ? 'upper-first' : 'lower-first'
    forecastCandles.push({
      ...item,
      x: x(lastIndex + index + 1),
      width: candleWidth,
      openY,
      closeY,
      highY,
      lowY,
      bodyTopY,
      bodyBottomY,
      bodyHeight: Math.max(2, Math.abs(closeY - openY)),
      upperWickHeight,
      lowerWickHeight,
      wickMode,
      bodyShift: wickMode === 'upper-first' ? -7 : 7,
      up: item.close >= item.open,
      animationIndex: index
	  })
	  const actualCandles = actualSource.map((item, index) => {
	    const openY = y(item.open)
	    const closeY = y(item.close)
	    return {
	      ...item,
	      x: x(lastIndex + index + 1),
	      width: Math.max(2, candleWidth * 0.54),
	      openY,
	      closeY,
	      highY: y(item.high),
	      lowY: y(item.low),
	      bodyTopY: Math.min(openY, closeY),
	      bodyHeight: Math.max(2, Math.abs(closeY - openY)),
	      up: item.close >= item.open
	    }
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
	    actualCandles,
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

const backtestSummary = computed(() => report.value?.backtest?.comparison || null)

const credibilityBreakdown = computed(() => {
  if (!report.value?.forecast || !report.value?.snapshot) return null
  const snapshot = report.value.snapshot
  const forecast = report.value.forecast
  const llm = report.value.llmProphecy || {}
  const events = report.value.events || {}
  const analog = report.value.analog || {}
  const close = Number(snapshot.close || 0)
  const ma5 = Number(snapshot.ma5 || close)
  const ma20 = Number(snapshot.ma20 || close)
  const ma60 = Number(snapshot.ma60 || close)
  const rsi = Number(snapshot.rsi14 || 50)
  const atr = Number(snapshot.atr14 || 0)
  const support = Number(snapshot.support || close)
  const resistance = Number(snapshot.resistance || close)
  const direction = forecast.direction
  const eventScore = Number(events.signal?.score || 0)
  const eventCount = Number(events.events?.length || 0)
  const analogUp = analog.upProbability == null ? 50 : Number(analog.upProbability)
  const sampleSize = Number(analog.sampleSize || 0)
  const riskDistance = close ? Math.min(
    Math.abs(close - support) / close * 100,
    Math.abs(resistance - close) / close * 100
  ) : 0
  const atrPct = close ? atr / close * 100 : 0

  const technicalAlignment = direction === 'bull'
    ? (close >= ma20 ? 18 : -8) + (ma5 >= ma20 ? 12 : -4) + (rsi >= 45 && rsi <= 68 ? 10 : rsi > 72 ? -8 : 2)
    : direction === 'bear'
      ? (close <= ma20 ? 18 : -8) + (ma5 <= ma20 ? 12 : -4) + (rsi <= 55 && rsi >= 32 ? 10 : rsi < 28 ? -8 : 2)
      : (Math.abs(close - ma20) / Math.max(close, 0.01) < 0.035 ? 18 : 6) + (rsi > 38 && rsi < 66 ? 14 : 2)
  const analogAlignment = direction === 'bull'
    ? (analogUp - 50) * 0.55
    : direction === 'bear'
      ? (50 - analogUp) * 0.55
      : (18 - Math.abs(analogUp - 50) * 0.35)
  const technicalScore = clampScore(52 + technicalAlignment + analogAlignment + Math.min(10, sampleSize / 4))

  const eventAlignment = direction === 'bull'
    ? eventScore * 2.1
    : direction === 'bear'
      ? -eventScore * 2.1
      : 8 - Math.abs(eventScore)
  const eventScoreValue = clampScore(50 + eventAlignment + Math.min(10, eventCount * 1.2))

  const llmScore = llm.status === 'ok'
    ? clampScore(48 + Number(llm.probability || forecast.probability || 50) * 0.52)
    : clampScore(42 + Number(forecast.probability || 50) * 0.24)

  const riskPenalty = Math.max(0, atrPct * 3.2) + Math.max(0, 3 - riskDistance) * 4
  const riskScore = clampScore(78 - riskPenalty + (direction === 'neutral' ? 5 : 0))

  const items = [
    {
      key: 'technical',
      name: '技术结构',
      score: technicalScore,
      tone: scoreTone(technicalScore),
      shortName: '技术',
      reason: direction === 'bull'
        ? `收盘价相对 MA20 ${close >= ma20 ? '占优' : '偏弱'}，MA5 ${ma5 >= ma20 ? '压在 MA20 上方' : '仍在修复中'}。`
        : direction === 'bear'
          ? `收盘价相对 MA20 ${close <= ma20 ? '偏弱' : '仍有支撑'}，MA5 ${ma5 <= ma20 ? '低于 MA20' : '尚未转弱'}。`
          : `价格围绕 MA20 的偏离度为 ${formatPct(close && ma20 ? (close - ma20) / close * 100 : 0)}，震荡结构权重更高。`,
      shortReason: `MA/RSI 与相似形态 ${technicalScore >= 72 ? '同向' : technicalScore >= 58 ? '部分同向' : '分歧较大'}`,
      detail: `RSI14 ${rsi.toFixed(2)}，相似形态上涨概率 ${analog.upProbability ?? '--'}%，样本 ${sampleSize}。`
    },
    {
      key: 'events',
      name: '事件驱动',
      score: eventScoreValue,
      tone: scoreTone(eventScoreValue),
      shortName: '事件',
      reason: events.signal?.summary || '本次没有足够强的新闻公告事件，事件面权重自动降低。',
      shortReason: eventCount ? `纳入 ${eventCount} 条事件，事件分 ${eventScore.toFixed(1)}` : '事件样本不足',
      detail: `事件分 ${eventScore.toFixed(2)}，已纳入 ${eventCount} 条新闻公告。`
    },
    {
      key: 'llm',
      name: '模型裁决',
      score: llmScore,
      tone: scoreTone(llmScore),
      shortName: '模型',
      reason: llm.status === 'ok'
        ? (llm.summary || '当前模型已参与方向裁决。')
        : '当前模型不可用或返回异常，本项由规则基线承接。',
      shortReason: llm.status === 'ok' ? `模型概率 ${llm.probability || forecast.probability || '--'}%` : '规则基线承接',
      detail: llm.status === 'ok'
        ? `${llmProviderLabel.value} 输出概率 ${llm.probability || forecast.probability || '--'}%。`
        : '建议配置真实 LLM 后再提高本项可信度。'
    },
    {
      key: 'risk',
      name: '风险边界',
      score: riskScore,
      tone: scoreTone(riskScore),
      shortName: '风险',
      reason: `支撑 ${support.toFixed(2)}，压力 ${resistance.toFixed(2)}，距离最近边界约 ${riskDistance.toFixed(2)}%。`,
      shortReason: `边界距离 ${riskDistance.toFixed(1)}%，ATR ${atrPct.toFixed(1)}%`,
      detail: `ATR 占比 ${atrPct.toFixed(2)}%，波动越大，预言可信度越保守。`
    }
  ]
  const score = Math.round(items.reduce((sum, item) => sum + item.score, 0) / items.length)
  const radar = buildRadarGeometry(items)
  return {
    score,
    label: score >= 72 ? '支撑较强' : score >= 58 ? '中等可信' : '谨慎参考',
    tone: scoreTone(score),
    summary: `本次 ${directionLabel(direction)} 预言由四层信号共同支撑，分数越高代表方向、事件、模型和风险边界越一致。`,
    radarAxes: radar.axes,
    radarGrid: radar.grid,
    radarPoints: radar.points,
    radarPolygon: radar.polygon,
    items
  }
})

const forecastInsights = computed(() => {
  const forecast = report.value?.forecast
  const candles = forecast?.candles || []
  if (!candles.length) return []
  const baseClose = Number(report.value?.snapshot?.close || candles[0].open || 0)
  return candles.map((item, index) => {
    const previousClose = Number(index > 0 ? candles[index - 1].close : baseClose)
    const open = Number(item.open)
    const high = Number(item.high)
    const low = Number(item.low)
    const close = Number(item.close)
    const bodyHigh = Math.max(open, close)
    const bodyLow = Math.min(open, close)
    const upperWick = Math.max(0, high - bodyHigh)
    const lowerWick = Math.max(0, bodyLow - low)
    const range = Math.max(0.01, high - low)
    const changePct = previousClose ? ((close - previousClose) / previousClose * 100) : 0
    const intradayPct = open ? ((close - open) / open * 100) : 0
    const upperRatio = upperWick / range
    const lowerRatio = lowerWick / range
    const wickMode = upperWick >= lowerWick ? 'upper-first' : 'lower-first'
    const direction = close >= open ? '收红' : '承压'
    const shape = wickMode === 'upper-first'
      ? upperRatio > 0.32 ? '冲高回落' : '上探后收敛'
      : lowerRatio > 0.32 ? '下探反弹' : '回踩后企稳'
    const tone = forecast.direction === 'bull'
      ? '主方向偏多'
      : forecast.direction === 'bear'
        ? '主方向偏空'
        : '主方向震荡'
    const story = wickMode === 'upper-first'
      ? `盘中先尝试上攻到 ${high.toFixed(2)}，随后资金兑现或阻力压制，价格回收到 ${close.toFixed(2)}，形成${shape}。`
      : `盘中先回踩到 ${low.toFixed(2)}，随后有承接修复，价格反弹到 ${close.toFixed(2)}，形成${shape}。`
    const wickNote = wickMode === 'upper-first'
      ? `上影占振幅 ${(upperRatio * 100).toFixed(0)}%，重点观察 ${high.toFixed(2)} 附近是否再次放量突破。`
      : `下影占振幅 ${(lowerRatio * 100).toFixed(0)}%，重点观察 ${low.toFixed(2)} 附近是否继续有承接。`
    const invalidNote = forecast.direction === 'bull'
      ? `跌破 ${low.toFixed(2)} 后，本日偏多预言失效。`
      : forecast.direction === 'bear'
        ? `突破 ${high.toFixed(2)} 后，本日偏空预言失效。`
        : `有效突破 ${high.toFixed(2)} 或跌破 ${low.toFixed(2)} 后，震荡预言失效。`
    return {
      index,
      day: item.day ?? index + 1,
      title: `${shape} · ${direction}`,
      story: `${tone}，${story}`,
      open: open.toFixed(2),
      high: high.toFixed(2),
      low: low.toFixed(2),
      close: close.toFixed(2),
      changePct: changePct.toFixed(2),
      wickNote,
      rangeNote: `日内振幅 ${(range / Math.max(0.01, open) * 100).toFixed(2)}%，开收变化 ${intradayPct.toFixed(2)}%。`,
      invalidNote
    }
  })
})

const selectedForecastInsight = computed(() => {
  if (!forecastInsights.value.length) return null
  const index = Math.min(selectedForecastIndex.value, forecastInsights.value.length - 1)
  return forecastInsights.value[index]
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
  if (form.mode === 'backtest' && !form.asOfDate) {
    error.value = '请选择回测日期'
    return
  }
  loading.value = true
  report.value = null
  selectedForecastIndex.value = 0
  error.value = ''
  startLoadingSteps()
  try {
    const payload = {
      symbol: form.symbol,
      horizon: form.horizon,
      days: form.days,
      provider: 'eastmoney'
    }
    const res = form.mode === 'backtest'
      ? await backtestStockProphecy({
          ...payload,
          asOfDate: form.asOfDate,
          useLlm: form.useBacktestLlm
        })
      : await generateStockProphecy({
          ...payload,
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

const clampScore = (value) => Math.max(0, Math.min(100, Math.round(Number(value) || 0)))

const scoreTone = (value) => {
  const score = Number(value) || 0
  if (score >= 72) return 'tone-bull'
  if (score >= 58) return 'tone-neutral'
  return 'tone-bear'
}

const buildRadarGeometry = (items) => {
  const center = 120
  const radius = 78
  const labelRadius = 103
  const angles = [-90, 0, 90, 180]
  const polar = (angle, distance) => {
    const radians = angle * Math.PI / 180
    return {
      x: Number((center + Math.cos(radians) * distance).toFixed(2)),
      y: Number((center + Math.sin(radians) * distance).toFixed(2))
    }
  }
  const axes = items.map((item, index) => {
    const edge = polar(angles[index], radius)
    const label = polar(angles[index], labelRadius)
    return {
      key: item.key,
      shortName: item.shortName,
      x: edge.x,
      y: edge.y,
      labelX: label.x,
      labelY: label.y + 4
    }
  })
  const grid = [0.33, 0.66, 1].map((scale) => angles
    .map((angle) => {
      const point = polar(angle, radius * scale)
      return `${point.x},${point.y}`
    })
    .join(' '))
  const points = items.map((item, index) => {
    const point = polar(angles[index], radius * clampScore(item.score) / 100)
    return { key: item.key, ...point }
  })
  return {
    axes,
    grid,
    points,
    polygon: points.map((point) => `${point.x},${point.y}`).join(' ')
  }
}

const formatPct = (value) => `${Number(value || 0).toFixed(2)}%`

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

.mode-switch {
  width: max-content;
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  padding: 4px;
  border: 1px solid color-mix(in srgb, var(--accent-2) 38%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--panel-solid) 72%, transparent);
}

.mode-switch.compact {
  width: 100%;
  margin-bottom: 14px;
}

.mode-switch button {
  height: 34px;
  min-width: 88px;
  border: 0;
  border-radius: 999px;
  color: var(--muted);
  background: transparent;
  font-size: 13px;
  font-weight: 900;
  cursor: pointer;
}

.mode-switch.compact button {
  min-width: 0;
}

.mode-switch button.active {
  color: var(--accent-ink);
  background: var(--accent-2);
  box-shadow: 0 0 18px color-mix(in srgb, var(--accent-2) 28%, transparent);
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

.live-kline-loader {
  display: grid;
  gap: 12px;
}

.loader-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 14px;
}

.loader-head span {
  color: var(--muted);
  font: 850 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.loader-head strong {
  color: var(--text);
  font-size: 14px;
  line-height: 1.35;
  text-align: right;
}

.loader-chart {
  position: relative;
  height: 210px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 20px;
  background:
    linear-gradient(0deg, var(--chart-grid) 1px, transparent 1px),
    linear-gradient(90deg, var(--chart-grid) 1px, transparent 1px),
    color-mix(in srgb, var(--panel-solid) 84%, transparent);
  background-size: 100% 42px, 42px 100%, auto;
}

.loader-chart::before {
  content: '';
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 28%;
  background: var(--forecast);
  border-left: 1px dashed color-mix(in srgb, var(--accent-2) 65%, transparent);
}

.loader-chart::after {
  content: '';
  position: absolute;
  left: 6%;
  right: 6%;
  top: 50%;
  height: 2px;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 62%, transparent), color-mix(in srgb, var(--accent-2) 46%, transparent), transparent);
  transform: translateY(-50%);
  opacity: 0.42;
}

.loader-candle {
  position: absolute;
  left: var(--x);
  bottom: var(--b);
  width: 9px;
  height: var(--h);
  border-radius: 999px;
  background: var(--accent);
  box-shadow: 0 -22px 0 -3px var(--accent), 0 22px 0 -3px var(--accent), 0 0 18px color-mix(in srgb, var(--accent) 26%, transparent);
  opacity: 0;
  transform: translateY(22px) scaleY(0.25);
  transform-origin: bottom center;
  animation: candleReplay 2.9s cubic-bezier(0.16, 1, 0.3, 1) infinite;
  animation-delay: var(--d);
}

.loader-candle.risk {
  background: var(--risk);
  box-shadow: 0 -22px 0 -3px var(--risk), 0 22px 0 -3px var(--risk);
}

.loader-candle.prophecy {
  width: 10px;
  background: var(--accent-2);
  box-shadow: 0 -26px 0 -3px var(--accent-2), 0 24px 0 -3px var(--accent-2), 0 0 22px color-mix(in srgb, var(--accent-2) 34%, transparent);
}

.scan-beam {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 72px;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--accent) 18%, transparent), transparent);
  filter: blur(1px);
  animation: scanBeam 2.9s linear infinite;
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

.chart-analysis-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(250px, 310px);
  gap: 14px;
  align-items: stretch;
}

.chart-main-column {
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
.up-fill {
  stroke: var(--accent);
}

.up-fill {
  fill: var(--accent);
}

.down,
.down-fill {
  stroke: var(--risk);
}

.down-fill {
  fill: var(--risk);
}

.forecast-band {
  fill: var(--forecast);
  opacity: 0;
  animation: prophecyZoneReveal 620ms ease forwards;
  animation-delay: 1.55s;
}

.forecast-divider {
  stroke: color-mix(in srgb, var(--accent-2) 86%, transparent);
  stroke-width: 1.4;
  stroke-dasharray: 5 5;
  opacity: 0;
  animation: prophecyZoneReveal 620ms ease forwards;
  animation-delay: 1.55s;
}

.forecast-label {
  opacity: 0;
  animation: prophecyZoneReveal 620ms ease forwards;
  animation-delay: 1.55s;
}

.candles line,
.candles rect {
  opacity: 0;
  transform-box: fill-box;
  transform-origin: center bottom;
  animation: candleReveal 520ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: var(--d);
}

.prophecy-candle {
  color: var(--risk);
  cursor: pointer;
  outline: none;
}

.prophecy-candle.is-up {
  color: var(--accent);
}

.prophecy-candle.is-down {
  color: var(--risk);
}

.prophecy-candle.active .forecast-wick,
.prophecy-candle.active .forecast-body,
.prophecy-candle:focus-visible .forecast-wick,
.prophecy-candle:focus-visible .forecast-body {
  filter: drop-shadow(0 0 13px color-mix(in srgb, var(--accent-2) 62%, transparent));
}

.forecast-wick,
.forecast-body,
.wick-flash {
  opacity: 0;
  transform-box: fill-box;
  vector-effect: non-scaling-stroke;
}

.forecast-wick {
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
}

.forecast-body {
  fill: currentColor;
  stroke: currentColor;
  stroke-width: 1;
}

.actual-candles line,
.actual-candles rect {
  stroke: color-mix(in srgb, var(--accent-2) 92%, var(--text));
  stroke-width: 2.2;
  opacity: 0.9;
  vector-effect: non-scaling-stroke;
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--accent-2) 28%, transparent));
}

.actual-candles rect {
  fill: color-mix(in srgb, var(--accent-2) 18%, transparent);
  stroke-dasharray: 3 2;
}

.upper-wick {
  transform-origin: center bottom;
}

.lower-wick {
  transform-origin: center top;
}

.upper-first .upper-wick {
  animation: prophecyUpperProbe 1120ms cubic-bezier(0.12, 0.82, 0.24, 1) forwards;
  animation-delay: var(--d);
}

.upper-first .forecast-body {
  animation: prophecyBodySettle 1040ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: calc(var(--d) + 0.52s);
}

.upper-first .lower-wick {
  animation: prophecyLowerAfter 820ms ease-out forwards;
  animation-delay: calc(var(--d) + 0.88s);
}

.lower-first .lower-wick {
  animation: prophecyLowerProbe 1120ms cubic-bezier(0.12, 0.82, 0.24, 1) forwards;
  animation-delay: var(--d);
}

.lower-first .forecast-body {
  animation: prophecyBodySettle 1040ms cubic-bezier(0.16, 1, 0.3, 1) forwards;
  animation-delay: calc(var(--d) + 0.52s);
}

.lower-first .upper-wick {
  animation: prophecyUpperAfter 820ms ease-out forwards;
  animation-delay: calc(var(--d) + 0.88s);
}

.wick-flash {
  fill: var(--accent-2);
  stroke: color-mix(in srgb, var(--accent-2) 72%, white);
  stroke-width: 1.2;
  filter: drop-shadow(0 0 10px color-mix(in srgb, var(--accent-2) 52%, transparent));
}

.upper-first .upper-flash,
.lower-first .lower-flash {
  animation: wickPulse 860ms ease-out forwards;
  animation-delay: calc(var(--d) + 0.24s);
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

.actual-dot {
  background: color-mix(in srgb, var(--accent-2) 74%, transparent);
  border: 1px solid var(--accent-2);
  box-shadow: 0 0 12px color-mix(in srgb, var(--accent-2) 32%, transparent);
}

.backtest-compare-panel {
  display: grid;
  grid-template-columns: minmax(150px, 0.24fr) minmax(0, 1fr);
  gap: 12px;
  margin-top: 14px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--accent-2) 42%, transparent);
  border-radius: 18px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent-2) 10%, transparent), transparent 44%),
    color-mix(in srgb, var(--panel-solid) 88%, transparent);
  box-shadow: inset 3px 0 0 color-mix(in srgb, var(--accent-2) 80%, transparent);
}

.compare-verdict {
  display: grid;
  align-content: center;
  gap: 6px;
  min-height: 92px;
}

.compare-verdict span,
.compare-verdict small,
.compare-metrics span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 780;
}

.compare-verdict strong {
  color: var(--text);
  font-size: 22px;
  line-height: 1.05;
}

.compare-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.compare-metrics div {
  display: grid;
  align-content: space-between;
  gap: 7px;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--soft);
}

.compare-metrics strong {
  color: var(--text);
  font: 850 15px/1.15 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-word;
}

.forecast-insight {
  display: grid;
  gap: 14px;
  margin-top: 16px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--accent-2) 42%, transparent);
  border-radius: 18px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent-2) 12%, transparent), transparent 42%),
    color-mix(in srgb, var(--panel-solid) 88%, transparent);
  box-shadow: inset 3px 0 0 color-mix(in srgb, var(--accent-2) 88%, transparent);
}

.insight-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 14px;
}

.insight-head span {
  color: var(--accent-2);
  font: 850 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.insight-head strong {
  color: var(--text);
  font-size: 18px;
  line-height: 1.2;
}

.forecast-insight p {
  max-width: 96ch;
  margin: 0;
  color: var(--text);
  font-size: 13px;
  line-height: 1.75;
}

.insight-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.insight-metrics div {
  display: grid;
  gap: 6px;
  min-width: 0;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--soft);
}

.insight-metrics span,
.insight-notes span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 760;
}

.insight-metrics strong {
  color: var(--text);
  font: 850 17px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.insight-notes {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.insight-notes span {
  min-width: 0;
  padding: 10px 11px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: color-mix(in srgb, var(--soft) 82%, transparent);
  line-height: 1.55;
}

.forecast-day-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.forecast-day-tabs button {
  width: 38px;
  height: 30px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  background: var(--soft);
  font: 850 12px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  cursor: pointer;
}

.forecast-day-tabs button.active,
.forecast-day-tabs button:hover {
  border-color: color-mix(in srgb, var(--accent-2) 74%, transparent);
  color: var(--text);
  background: color-mix(in srgb, var(--accent-2) 18%, transparent);
  box-shadow: 0 0 16px color-mix(in srgb, var(--accent-2) 18%, transparent);
}

.credibility-radar-panel {
  display: grid;
  grid-template-rows: auto minmax(0, auto) 1fr;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 16px;
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--accent-2) 12%, transparent), transparent 48%),
    color-mix(in srgb, var(--panel-solid) 88%, transparent);
  box-shadow: inset 3px 0 0 color-mix(in srgb, var(--accent-2) 78%, transparent);
}

.radar-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.radar-head div {
  display: grid;
  gap: 4px;
}

.radar-head span,
.radar-head b,
.radar-legend-list span {
  color: var(--muted);
  font-size: 12px;
  font-weight: 820;
}

.radar-head strong {
  color: var(--text);
  font: 950 42px/0.95 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.radar-head b {
  color: var(--accent-2);
  text-align: right;
}

.credibility-radar {
  width: min(100%, 250px);
  aspect-ratio: 1;
  justify-self: center;
}

.radar-grid-shape {
  fill: none;
  stroke: color-mix(in srgb, var(--muted) 28%, transparent);
  stroke-width: 1;
}

.radar-axis {
  stroke: color-mix(in srgb, var(--muted) 24%, transparent);
  stroke-width: 1;
}

.radar-score-shape {
  fill: color-mix(in srgb, var(--accent) 22%, transparent);
  stroke: color-mix(in srgb, var(--accent) 86%, transparent);
  stroke-width: 2;
  filter: drop-shadow(0 0 14px color-mix(in srgb, var(--accent) 22%, transparent));
}

.radar-point {
  fill: var(--accent-2);
  stroke: color-mix(in srgb, var(--panel-solid) 92%, black);
  stroke-width: 1.4;
}

.radar-label {
  fill: var(--muted);
  font-size: 11px;
  font-weight: 850;
}

.radar-center-score {
  fill: var(--text);
  font: 950 24px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.radar-center-label {
  fill: var(--muted);
  font-size: 10px;
  font-weight: 820;
}

.radar-legend-list {
  display: grid;
  gap: 9px;
}

.radar-legend-list div {
  display: grid;
  grid-template-columns: 44px 34px minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  padding: 8px 9px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: color-mix(in srgb, var(--soft) 82%, transparent);
}

.radar-legend-list strong {
  color: var(--text);
  font: 900 15px/1 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.radar-legend-list p {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.4;
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

@keyframes candleReplay {
  0% {
    opacity: 0;
    transform: translateY(22px) scaleY(0.25);
  }
  16% {
    opacity: 1;
    transform: translateY(0) scaleY(1);
  }
  72% {
    opacity: 1;
    transform: translateY(0) scaleY(1);
  }
  100% {
    opacity: 0;
    transform: translateY(-8px) scaleY(0.92);
  }
}

@keyframes scanBeam {
  from { transform: translateX(-90px); }
  to { transform: translateX(620px); }
}

@keyframes candleReveal {
  from {
    opacity: 0;
    transform: translateY(12px) scaleY(0.35);
  }
  to {
    opacity: 1;
    transform: translateY(0) scaleY(1);
  }
}

@keyframes prophecyReveal {
  from {
    opacity: 0;
    transform: translateY(18px) scaleY(0.15);
    filter: drop-shadow(0 0 0 transparent);
  }
  48% {
    opacity: 1;
    transform: translateY(-3px) scaleY(1.08);
    filter: drop-shadow(0 0 12px color-mix(in srgb, var(--accent-2) 46%, transparent));
  }
  to {
    opacity: 0.95;
    transform: translateY(0) scaleY(1);
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--accent-2) 34%, transparent));
  }
}

@keyframes prophecyUpperProbe {
  from {
    opacity: 0;
    transform: translateY(9px) scaleY(0.08);
    filter: drop-shadow(0 0 0 transparent);
  }
  62% {
    opacity: 1;
    transform: translateY(-4px) scaleY(1.08);
    filter: drop-shadow(0 0 14px color-mix(in srgb, var(--accent-2) 50%, transparent));
  }
  to {
    opacity: 0.96;
    transform: translateY(0) scaleY(1);
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--accent-2) 34%, transparent));
  }
}

@keyframes prophecyLowerProbe {
  from {
    opacity: 0;
    transform: translateY(-9px) scaleY(0.08);
    filter: drop-shadow(0 0 0 transparent);
  }
  62% {
    opacity: 1;
    transform: translateY(4px) scaleY(1.08);
    filter: drop-shadow(0 0 14px color-mix(in srgb, var(--accent-2) 50%, transparent));
  }
  to {
    opacity: 0.96;
    transform: translateY(0) scaleY(1);
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--accent-2) 34%, transparent));
  }
}

@keyframes prophecyUpperAfter {
  from {
    opacity: 0;
    transform: translateY(5px) scaleY(0.08);
  }
  to {
    opacity: 0.9;
    transform: translateY(0) scaleY(1);
  }
}

@keyframes prophecyLowerAfter {
  from {
    opacity: 0;
    transform: translateY(-5px) scaleY(0.08);
  }
  to {
    opacity: 0.9;
    transform: translateY(0) scaleY(1);
  }
}

@keyframes prophecyBodySettle {
  from {
    opacity: 0;
    transform: translateY(var(--body-shift)) scaleY(0.18);
    filter: drop-shadow(0 0 0 transparent);
  }
  54% {
    opacity: 1;
    transform: translateY(calc(var(--body-shift) * -0.18)) scaleY(1.12);
    filter: drop-shadow(0 0 13px color-mix(in srgb, currentColor 36%, transparent));
  }
  to {
    opacity: 0.94;
    transform: translateY(0) scaleY(1);
    filter: drop-shadow(0 0 8px color-mix(in srgb, currentColor 28%, transparent));
  }
}

@keyframes wickPulse {
  from {
    opacity: 0;
    transform: scale(0.34);
  }
  42% {
    opacity: 0.95;
    transform: scale(1.25);
  }
  to {
    opacity: 0;
    transform: scale(2.15);
  }
}

@keyframes prophecyZoneReveal {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
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

	  .loader-candle,
	  .candles line,
	  .candles rect,
	  .forecast-candles line,
	  .forecast-candles rect,
	  .forecast-body,
	  .forecast-wick,
	  .forecast-band,
	  .forecast-divider,
	  .forecast-label {
	    opacity: 1 !important;
	    transform: none !important;
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

  .chart-analysis-layout {
    grid-template-columns: 1fr;
  }

  .credibility-radar-panel {
    grid-template-columns: minmax(210px, 0.42fr) minmax(0, 1fr);
    grid-template-rows: auto 1fr;
    align-items: center;
  }

  .radar-head {
    grid-column: 1 / -1;
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
  .insight-metrics,
  .insight-notes,
  .backtest-compare-panel,
  .compare-metrics,
  .metric-grid,
  .agent-row {
    grid-template-columns: 1fr;
  }

  .credibility-radar-panel,
  .radar-legend-list div {
    grid-template-columns: 1fr;
  }

  .insight-head {
    align-items: start;
    flex-direction: column;
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
