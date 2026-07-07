<script setup lang="ts">
import type { ClassColor } from '@/types/segmentation'

defineProps<{
  classes: ClassColor[]
}>()
</script>

<template>
  <div class="legend">
    <div class="legend-title">类别图例</div>
    <div class="legend-items">
      <div v-for="c in classes" :key="c.id" class="legend-item">
        <span class="swatch" :style="{ backgroundColor: c.color }"></span>
        <span class="name">{{ c.name }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.legend {
  border: 1px solid var(--seg-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  background: var(--seg-surface);
}
.legend-title {
  font-size: 0.85rem;
  color: var(--seg-text-muted);
  margin-bottom: 0.6rem;
}
.legend-items {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.4rem 0.8rem;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.82rem;
}
.swatch {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid var(--seg-border);
  flex-shrink: 0;
}
.name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
