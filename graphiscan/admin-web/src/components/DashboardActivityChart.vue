<template>
  <figure class="activity-chart" @mouseleave="hovered = null">
    <div class="chart-readout" aria-live="polite">
      <template v-if="selected"><strong>{{ selected.label }}</strong><span>{{ selected.count }} {{ selected.count === 1 ? 'screening' : 'screenings' }}</span></template>
      <span v-else class="chart-guidance">Hover or select a day to see its count.</span>
    </div>
    <svg viewBox="0 0 600 170" role="group" aria-label="Daily screening activity" preserveAspectRatio="none">
      <title>{{ activity.description }}</title>
      <defs><linearGradient id="dashboard-activity-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="currentColor" stop-opacity=".16" /><stop offset="100%" stop-color="currentColor" stop-opacity="0" /></linearGradient></defs>
      <g class="chart-grid"><line v-for="y in [20,70,120]" :key="y" x1="0" :y1="y" x2="600" :y2="y" /></g>
      <text x="0" y="13">{{ activity.maximum }}</text><text x="0" y="164">0</text>
      <path :d="activity.area" fill="url(#dashboard-activity-fill)" />
      <polyline :points="activity.points" fill="none" stroke="currentColor" stroke-width="2.5" vector-effect="non-scaling-stroke" stroke-linecap="round" stroke-linejoin="round" />
      <line v-if="active !== null" :x1="activity.coordinates[active].x" y1="18" :x2="activity.coordinates[active].x" y2="150" class="chart-guide" />
      <g v-for="(point,index) in activity.coordinates" :key="activity.days[index].key" class="chart-day" role="button" tabindex="0" :aria-label="activity.days[index].label + ': ' + activity.days[index].count + ' screenings'" :aria-pressed="pinned === index" @mouseenter="hovered = index" @focus="hovered = index" @blur="hovered = null" @click="toggle(index)" @keydown.enter.prevent="toggle(index)" @keydown.space.prevent="toggle(index)" @keydown.esc="pinned = null; hovered = null">
        <rect :x="index === 0 ? 0 : point.x - 46" y="16" :width="index === 0 || index === 6 ? 58 : 92" height="136" rx="6" class="chart-hit" />
        <circle :cx="point.x" :cy="point.y" :r="active === index ? 6 : 3.5" fill="white" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke" />
      </g>
    </svg>
    <figcaption><span v-for="day in activity.days" :key="day.key">{{ day.label }}</span></figcaption>
  </figure>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
const props=defineProps({activity:{type:Object,required:true}})
const hovered=ref(null),pinned=ref(null)
const active=computed(()=>hovered.value ?? pinned.value)
const selected=computed(()=>active.value === null ? null : props.activity.days[active.value])
function toggle(index){pinned.value=pinned.value === index ? null : index}
watch(()=>props.activity,()=>{hovered.value=null;pinned.value=null})
</script>
<style scoped>
.activity-chart{display:flex;flex-direction:column;gap:6px;flex:1;min-height:0;min-width:0;margin:0;color:var(--blue-700)}
.chart-readout{display:flex;align-items:center;gap:10px;min-height:20px;flex:none;font:12px/20px var(--font-ui)}
.chart-readout strong{font-weight:600}.chart-readout span{color:var(--muted)}
.activity-chart svg{display:block;flex:1;min-height:0;width:100%;overflow:visible}
.activity-chart svg text{fill:var(--muted);font:11px var(--font-ui)}
.chart-grid line{stroke:var(--border);stroke-dasharray:4 6}
.chart-guide{stroke:currentColor;stroke-opacity:.35;stroke-dasharray:4 4;vector-effect:non-scaling-stroke}
.chart-day{cursor:pointer;outline:none}.chart-hit{fill:transparent;stroke:transparent}
.chart-day:focus-visible .chart-hit{fill:var(--blue-50);fill-opacity:.5;stroke:currentColor;stroke-width:1;vector-effect:non-scaling-stroke}
figcaption{display:flex;justify-content:space-between;gap:4px;flex:none;color:var(--muted);font:10px/16px var(--font-ui)}
@media(max-width:850px){.activity-chart{flex:none;min-height:150px}.activity-chart svg{height:110px;flex:none}figcaption{font-size:9px}.chart-guidance{font-size:11px}}
</style>
