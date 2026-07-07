<script setup lang="ts">
import type { SampleImage } from '@/types/segmentation'

defineProps<{
  images: SampleImage[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  upload: [file: File]
}>()

function onUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  emit('upload', file)
  input.value = ''
}
</script>

<template>
  <div class="picker">
    <div class="picker-head">
      <span class="picker-title">选择图片</span>
      <label class="upload-btn">
        本地上传
        <input type="file" accept="image/*" hidden @change="onUpload" />
      </label>
    </div>
    <div class="thumbs">
      <button
        v-for="img in images"
        :key="img.id"
        class="thumb"
        :class="{ active: img.id === modelValue }"
        :title="img.name"
        @click="emit('update:modelValue', img.id)"
      >
        <img :src="img.thumbnailUrl" :alt="img.name" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.picker {
  border: 1px solid var(--seg-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  background: var(--seg-surface);
}
.picker-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.7rem;
}
.picker-title {
  font-size: 0.85rem;
  color: var(--seg-text-muted);
}
.upload-btn {
  font-size: 0.78rem;
  padding: 0.3rem 0.6rem;
  border: 1px solid var(--seg-border);
  border-radius: 6px;
  cursor: pointer;
  color: var(--seg-accent);
}
.upload-btn:hover {
  background: var(--seg-surface-2);
}
.thumbs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(64px, 1fr));
  gap: 0.5rem;
}
.thumb {
  padding: 0;
  border: 2px solid transparent;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: none;
  line-height: 0;
}
.thumb img {
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
  display: block;
}
.thumb.active {
  border-color: var(--seg-accent);
}
</style>
