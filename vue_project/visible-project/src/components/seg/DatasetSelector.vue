<script setup lang="ts">
import type { DatasetInfo } from '@/types/segmentation'

defineProps<{
  datasets: DatasetInfo[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

function onChange(e: Event) {
  emit('update:modelValue', (e.target as HTMLSelectElement).value)
}
</script>

<template>
  <label class="field">
    <span class="field-label">数据集</span>
    <select class="field-input" :value="modelValue" @change="onChange">
      <option v-for="d in datasets" :key="d.id" :value="d.id">
        {{ d.name }}（{{ d.numClasses }} 类）
      </option>
    </select>
  </label>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.field-label {
  font-size: 0.8rem;
  color: var(--seg-text-muted);
}
.field-input {
  padding: 0.5rem 0.65rem;
  border-radius: 8px;
  border: 1px solid var(--seg-border);
  background: var(--seg-surface);
  color: var(--seg-text);
  font-size: 0.9rem;
}
</style>
