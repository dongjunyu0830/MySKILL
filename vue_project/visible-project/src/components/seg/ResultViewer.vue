<script setup lang="ts">
import { ref } from 'vue'
import type { PredictionResult } from '@/types/segmentation'

defineProps<{
  result: PredictionResult
}>()

// 叠加图的预测层透明度，实时可调（对应"预测结果与原图叠加"要求）
const opacity = ref(0.5)
</script>

<template>
  <div class="viewer">
    <div class="panels">
      <figure class="panel">
        <img :src="result.originalUrl" alt="原图" />
        <figcaption>原图</figcaption>
      </figure>

      <figure class="panel">
        <img :src="result.predictionUrl" alt="预测图" />
        <figcaption>预测分割图</figcaption>
      </figure>

      <figure class="panel">
        <div class="overlay-stack">
          <img :src="result.originalUrl" alt="原图" />
          <img
            class="overlay-top"
            :src="result.predictionUrl"
            :style="{ opacity }"
            alt="叠加"
          />
        </div>
        <figcaption>叠加（透明度 {{ Math.round(opacity * 100) }}%）</figcaption>
      </figure>
    </div>

    <div class="controls">
      <label class="slider-label">
        叠加透明度
        <input v-model.number="opacity" type="range" min="0" max="1" step="0.05" />
      </label>
      <span class="infer">推理耗时：{{ result.inferenceMs }} ms</span>
    </div>
  </div>
</template>

<style scoped>
.viewer {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
.panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}
.panel {
  margin: 0;
  border: 1px solid var(--seg-border);
  border-radius: 10px;
  overflow: hidden;
  background: var(--seg-surface);
}
.panel img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}
.panel figcaption {
  padding: 0.5rem;
  text-align: center;
  font-size: 0.82rem;
  color: var(--seg-text-muted);
}
.overlay-stack {
  position: relative;
  line-height: 0;
}
.overlay-stack .overlay-top {
  position: absolute;
  inset: 0;
}
.controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}
.slider-label {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.85rem;
  color: var(--seg-text-muted);
}
.slider-label input {
  width: 200px;
}
.infer {
  font-size: 0.82rem;
  color: var(--seg-text-muted);
}
</style>
