<template>
  <section ref="chartRoot" class="screening-trend" aria-label="Recorded screening results, oldest to newest" :aria-busy="busy">
    <div class="trend-chart" :class="{ 'keyboard-selection': keyboardSelection }">
      <div class="trend-labels" aria-hidden="true">
        <span v-for="level in levels" :key="level.label" :style="{ top: level.y + '%' }">{{ level.label }}</span>
      </div>
      <div ref="plotRoot" class="trend-plot" @pointerleave="dismissHover" @keydown.esc="inspecting = false">
        <svg class="trend-grid" viewBox="0 0 1000 200" preserveAspectRatio="none" aria-hidden="true">
          <line v-for="level in levels" :key="level.label" x1="0" :y1="level.y * 2" x2="1000" :y2="level.y * 2" />
        </svg>
        <div v-if="ordered.length" :key="seriesKey" class="trend-data">
          <svg class="trend-lines" viewBox="0 0 1000 200" preserveAspectRatio="none" aria-hidden="true">
            <polyline v-for="(segment,index) in segments" :key="index" :points="segment" class="trend-line" fill="none" vector-effect="non-scaling-stroke" />
          </svg>
          <button v-for="(point,index) in ordered" :key="point.id"
            type="button" class="trend-point" :class="{ selected: active?.id === point.id, unknown: point.kind === 2 }"
            :style="{ left: point.x + '%', top: point.y + '%' }"
            :tabindex="active?.id === point.id ? 0 : -1" :aria-pressed="active?.id === point.id"
            :aria-label="pointLabel(point)" :disabled="busy"
            @pointerenter="inspect(point, $event)" @focus="inspect(point)"
            @click="inspect(point)" @blur="inspecting = false"
            @keydown.left.prevent="selectPoint(index - 1)" @keydown.right.prevent="selectPoint(index + 1)"
            @keydown.home.prevent="selectPoint(0)" @keydown.end.prevent="selectPoint(ordered.length - 1)">
            <span class="trend-dot"></span>
          </button>
        </div>
        <div v-if="active && inspecting && !busy" class="trend-guide" :style="{ transform: 'translateX(' + active.x * plotSize.width / 100 + 'px)' }" aria-hidden="true"></div>
        <Transition name="trend-detail">
          <div v-if="active && inspecting && !busy" class="trend-tooltip" :style="tooltipStyle" aria-hidden="true">
            <span>{{ screeningLabel(active.row) }} <span class="trend-tooltip-date">{{ shortDate(active.row.date_generated, true) }}</span></span>
            <strong>{{ active.row.classification || 'Not recorded' }}</strong>
          </div>
        </Transition>
      </div>
      <div class="trend-axis-caption" aria-hidden="true">Screenings</div>
      <div class="trend-dates" aria-hidden="true">
        <span v-for="point in ticks" :key="point.id" :style="{ left: point.x + '%' }" :class="{ selected: active?.id === point.id }">
          <time>{{ shortDate(point.row.date_generated) }}</time><small>{{ screeningLabel(point.row) }}</small>
        </span>
      </div>
    </div>
    <span class="trend-accessible" role="status">{{ inspecting && active ? pointLabel(active) : '' }}</span>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { formatReportType } from '../utils/hosted-screenings.mjs'

const props = defineProps({ rows: { type: Array, required: true }, busy: Boolean })
const chartRoot = ref(null), plotRoot = ref(null)
const selectedId = ref(''), inspecting = ref(false), keyboardSelection = ref(false)
const plotSize = ref({ width: 600, height: 200 })
let resizeObserver

function kind(row) {
  const label = String(row.classification || '').trim().toLowerCase()
  return label === 'high potential' ? 0 : label === 'normal' ? 1 : 2
}
const ordered = computed(() => props.rows
  .map((row, index) => ({ row, index, time: Date.parse(row.date_generated) }))
  .sort((a, b) => (Number.isFinite(a.time) ? a.time : Infinity) - (Number.isFinite(b.time) ? b.time : Infinity) || a.index - b.index)
  .map(({ row }, index, all) => ({
    row, id: String(row.result_id), kind: kind(row),
    x: all.length === 1 ? 50 : 7 + index * 86 / (all.length - 1),
    y: [24, 65, 89][kind(row)],
  })))
const seriesKey = computed(() => ordered.value.map(point => [point.id, point.row.student_id, point.row.date_generated, point.row.classification].join(':')).join('|'))
const active = computed(() => ordered.value.find(point => point.id === selectedId.value) || ordered.value.at(-1))
const levels = computed(() => [
  { label: 'High Potential', y: 24 },
  { label: 'Normal', y: 65 },
  ...(ordered.value.some(point => point.kind === 2) ? [{ label: 'Other / unknown', y: 89 }] : []),
])
const segments = computed(() => {
  const result = []
  let current = []
  for (const point of ordered.value) {
    if (point.kind === 2) {
      if (current.length > 1) result.push(current.join(' '))
      current = []
    } else current.push(point.x * 10 + ',' + point.y * 2)
  }
  if (current.length > 1) result.push(current.join(' '))
  return result
})
const ticks = computed(() => {
  const count = Math.min(ordered.value.length, Math.max(2, Math.floor(plotSize.value.width / 105)))
  if (ordered.value.length <= count) return ordered.value
  return Array.from({ length: count }, (_, index) => ordered.value[Math.round(index * (ordered.value.length - 1) / (count - 1))])
})
const tooltipStyle = computed(() => {
  if (!active.value) return {}
  const width = Math.min(210, plotSize.value.width)
  const x = Math.max(0, Math.min(plotSize.value.width - width, active.value.x * plotSize.value.width / 100 - width / 2))
  const y = active.value.y * plotSize.value.height / 100 + (active.value.kind === 0 ? 22 : -76)
  return { width: width + 'px', transform: 'translate3d(' + x + 'px,' + Math.max(0, y) + 'px,0)' }
})
function shortDate(value, year = false) {
  const date = new Date(value)
  return value && Number.isFinite(date.getTime())
    ? date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', ...(year ? { year: 'numeric' } : {}) })
    : 'Date unknown'
}
function screeningLabel(row) {
  return row.report?.report_type === 'Initial Screening' ? 'Initial' : row.report?.report_type === 'Follow-up Screening' ? 'Follow-up' : 'Screening'
}
function pointLabel(point) {
  return formatReportType(point.row.report?.report_type) + ', ' + shortDate(point.row.date_generated, true) + ', ' + (point.row.classification || 'Model output not recorded')
}
function inspect(point, event) {
  if (props.busy || event?.pointerType === 'touch') return
  if (event) keyboardSelection.value = false
  selectedId.value = point.id
  inspecting.value = true
}
function dismissHover() {
  if (!plotRoot.value?.contains(document.activeElement)) inspecting.value = false
}
async function selectPoint(index) {
  const next = Math.max(0, Math.min(ordered.value.length - 1, index))
  if (!ordered.value[next]) return
  keyboardSelection.value = true
  selectedId.value = ordered.value[next].id
  inspecting.value = true
  await nextTick()
  chartRoot.value?.querySelectorAll('.trend-point')[next]?.focus({ preventScroll: true })
}
watch(seriesKey, () => {
  if (!ordered.value.some(point => point.id === selectedId.value)) selectedId.value = ordered.value.at(-1)?.id || ''
  inspecting.value = false
})
onMounted(() => {
  resizeObserver = new ResizeObserver(([entry]) => {
    plotSize.value = { width: entry.contentRect.width, height: entry.contentRect.height }
  })
  resizeObserver.observe(plotRoot.value)
})
onBeforeUnmount(() => resizeObserver?.disconnect())
</script>

<style scoped>
.screening-trend { width:100%; min-width:0; color:var(--blue-700); }
.trend-chart { display:grid; grid-template-columns:100px minmax(0,1fr); grid-template-rows:var(--progress-plot-height,200px) 42px; column-gap:20px; }
.trend-labels { position:relative; }
.trend-labels span { position:absolute; inset-inline:0; transform:translateY(-50%); color:var(--muted); font:500 12px/1.4 var(--font-ui); }
.trend-plot { position:relative; min-width:0; }
.trend-grid,.trend-lines { display:block; position:absolute; inset:0; width:100%; height:100%; overflow:visible; }
.trend-grid line { stroke:var(--border-soft); stroke-width:1; vector-effect:non-scaling-stroke; stroke-dasharray:3 5; }
.trend-data { position:absolute; inset:0; }
.trend-lines { animation:trend-draw 280ms var(--admin-motion-ease,cubic-bezier(.23,1,.32,1)) both; }
.trend-line { stroke:var(--blue-700); stroke-width:2.5; stroke-linecap:round; stroke-linejoin:round; }
.screening-trend .trend-point { position:absolute; display:grid; place-items:center; width:44px; height:44px; min-height:44px; padding:0; border:0; border-radius:50%; background:transparent; transform:translate(-50%,-50%); cursor:pointer; z-index:2; box-shadow:none; }
.trend-dot { display:block; width:10px; height:10px; border:2px solid var(--blue-700); border-radius:50%; background:var(--white); box-shadow:0 0 0 4px var(--white); transition:transform 160ms var(--admin-motion-ease,cubic-bezier(.23,1,.32,1)),background-color 160ms ease,box-shadow 160ms ease; animation:trend-points 240ms var(--admin-motion-ease,cubic-bezier(.23,1,.32,1)) both; }
.trend-point.selected .trend-dot { background:var(--blue-700); transform:scale(1.2); box-shadow:0 0 0 4px var(--white),0 0 0 8px var(--blue-50); }
.trend-point.unknown .trend-dot { border-color:var(--muted); border-radius:3px; }
.trend-point.unknown.selected .trend-dot { background:var(--muted); }
.trend-point:focus-visible { outline:2px solid var(--blue-700); outline-offset:0; }
.trend-point:disabled { cursor:default; }
.trend-guide { position:absolute; top:0; bottom:0; left:0; border-left:1px dashed var(--blue-300); pointer-events:none; transition:transform 160ms var(--admin-motion-ease,cubic-bezier(.23,1,.32,1)); }
.trend-tooltip { position:absolute; top:0; left:0; z-index:3; pointer-events:none; display:grid; gap:6px; padding:10px 12px; border:1px solid var(--border); border-radius:8px; background:var(--white); box-shadow:0 4px 14px rgb(38 52 69 / 7%); color:var(--text); transition:transform 160ms var(--admin-motion-ease,cubic-bezier(.23,1,.32,1)); }
.trend-tooltip>span { display:flex; justify-content:space-between; gap:10px; font:500 11px/16px var(--font-ui); }
.trend-tooltip-date { color:var(--muted); font-weight:400; }
.trend-tooltip strong { font:600 13px/18px var(--font-ui); overflow-wrap:anywhere; }
.trend-detail-enter-active,.trend-detail-leave-active { transition:opacity 140ms ease; }
.trend-detail-enter-from,.trend-detail-leave-to { opacity:0; }
.trend-axis-caption { align-self:start; padding-top:9px; color:var(--muted); font:400 11px/16px var(--font-ui); }
.trend-dates { position:relative; min-width:0; border-top:1px solid var(--border); }
.trend-dates>span { position:absolute; top:8px; transform:translateX(-50%); display:grid; gap:2px; text-align:center; white-space:nowrap; color:var(--muted); font:400 11px/14px var(--font-ui); }
.trend-dates>span.selected time { color:var(--blue-700); font-weight:600; }
.trend-dates small { font:inherit; font-size:10px; color:var(--muted); }
.trend-accessible { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); white-space:nowrap; }
.keyboard-selection :is(.trend-dot,.trend-guide,.trend-tooltip) { transition:none; }
@keyframes trend-draw { from { clip-path:inset(-12px 100% -12px -12px); opacity:.2; } to { clip-path:inset(-12px -12px -12px -12px); opacity:1; } }
@keyframes trend-points { from { opacity:0; } to { opacity:1; } }
@media(hover:hover) and (pointer:fine) { .trend-point:hover .trend-dot { transform:scale(1.3); box-shadow:0 0 0 4px var(--white),0 0 0 8px var(--blue-50); } }
@media(prefers-reduced-motion:reduce) { .trend-lines,.trend-dot { animation:none; } .trend-dot,.trend-guide,.trend-tooltip,.trend-detail-enter-active,.trend-detail-leave-active { transition:none; } }
@media(max-width:700px) { .trend-chart { grid-template-columns:76px minmax(0,1fr); column-gap:12px; } .trend-labels span { font-size:11px; } .trend-axis-caption { font-size:10px; } .trend-tooltip { padding:8px; } .trend-tooltip>span { gap:6px; font-size:10px; } }
</style>
