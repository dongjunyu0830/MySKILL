<script setup lang="ts">
import type { EvaluationResult } from '@/types/segmentation'

defineProps<{
  result: EvaluationResult
}>()

function pct(v: number): string {
  return (v * 100).toFixed(2) + '%'
}
</script>

<template>
  <div class="metrics">
    <div class="cards">
      <div class="card">
        <div class="card-label">mIoU</div>
        <div class="card-value">{{ pct(result.mIoU) }}</div>
      </div>
      <div class="card">
        <div class="card-label">Precision</div>
        <div class="card-value">{{ pct(result.precision) }}</div>
      </div>
      <div class="card">
        <div class="card-label">Recall</div>
        <div class="card-value">{{ pct(result.recall) }}</div>
      </div>
      <div class="card">
        <div class="card-label">F1</div>
        <div class="card-value">{{ pct(result.f1) }}</div>
      </div>
    </div>

    <p class="samples">测试样本数：{{ result.numSamples }}</p>

    <table class="per-class">
      <thead>
        <tr>
          <th>类别</th>
          <th>IoU</th>
          <th>Precision</th>
          <th>Recall</th>
          <th>F1</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in result.perClass" :key="c.classId">
          <td class="cls">
            <span class="swatch" :style="{ backgroundColor: c.color }"></span>
            {{ c.className }}
          </td>
          <td>
            <div class="bar-wrap">
              <div class="bar" :style="{ width: pct(c.iou) }"></div>
              <span class="bar-text">{{ pct(c.iou) }}</span>
            </div>
          </td>
          <td>{{ pct(c.precision) }}</td>
          <td>{{ pct(c.recall) }}</td>
          <td>{{ pct(c.f1) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.metrics {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
}
.card {
  border: 1px solid var(--seg-border);
  border-radius: 10px;
  padding: 1rem;
  background: var(--seg-surface);
  text-align: center;
}
.card-label {
  font-size: 0.8rem;
  color: var(--seg-text-muted);
}
.card-value {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--seg-accent);
  margin-top: 0.35rem;
}
.samples {
  font-size: 0.82rem;
  color: var(--seg-text-muted);
  margin: 0;
}
.per-class {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}
.per-class th,
.per-class td {
  padding: 0.5rem 0.6rem;
  border-bottom: 1px solid var(--seg-border);
  text-align: left;
}
.per-class th {
  color: var(--seg-text-muted);
  font-weight: 600;
}
.cls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid var(--seg-border);
  flex-shrink: 0;
}
.bar-wrap {
  position: relative;
  background: var(--seg-surface-2);
  border-radius: 5px;
  height: 18px;
  min-width: 120px;
  overflow: hidden;
}
.bar {
  height: 100%;
  background: var(--seg-accent);
  opacity: 0.8;
}
.bar-text {
  position: absolute;
  left: 6px;
  top: 0;
  line-height: 18px;
  font-size: 0.72rem;
  color: var(--seg-text);
}
</style>
