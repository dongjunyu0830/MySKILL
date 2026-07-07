<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'
import { listSampleImages } from '@/services/segmentationApi'
import type { SampleImage } from '@/types/segmentation'
import DatasetSelector from '@/components/seg/DatasetSelector.vue'
import ModelSelector from '@/components/seg/ModelSelector.vue'
import ImagePicker from '@/components/seg/ImagePicker.vue'
import ResultViewer from '@/components/seg/ResultViewer.vue'
import ClassLegend from '@/components/seg/ClassLegend.vue'

const store = useAppStore()
const { datasets, models, currentDatasetId, currentModelId, currentDataset, prediction, predicting } =
  storeToRefs(store)

const sampleImages = ref<SampleImage[]>([])
const selectedImageId = ref<string>('')
const uploadedFile = ref<File | null>(null)

async function loadSamples() {
  sampleImages.value = await listSampleImages(currentDatasetId.value)
  selectedImageId.value = sampleImages.value[0]?.id ?? ''
  uploadedFile.value = null
}

onMounted(async () => {
  await store.loadMeta()
  await loadSamples()
})

watch(currentDatasetId, () => {
  loadSamples()
})

function onSelectDataset(id: string) {
  store.setDataset(id)
}
function onSelectModel(id: string) {
  store.setModel(id)
}
function onUpload(file: File) {
  uploadedFile.value = file
  selectedImageId.value = ''
}

const selectedSample = computed(() => {
  if (uploadedFile.value) return null
  const img = sampleImages.value.find((i) => i.id === selectedImageId.value)
  return img?.name ?? null
})

const canPredict = computed(() => !!uploadedFile.value || !!selectedSample.value)

async function onPredict() {
  if (uploadedFile.value) {
    await store.runPredict({ file: uploadedFile.value })
  } else if (selectedSample.value) {
    await store.runPredict({ sample: selectedSample.value })
  }
}
</script>

<template>
  <section class="page">
    <div class="toolbar">
      <DatasetSelector
        :datasets="datasets"
        :model-value="currentDatasetId"
        @update:model-value="onSelectDataset"
      />
      <ModelSelector
        :models="models"
        :model-value="currentModelId"
        @update:model-value="onSelectModel"
      />
      <button class="predict-btn" :disabled="predicting || !canPredict" @click="onPredict">
        {{ predicting ? '预测中…' : '开始预测' }}
      </button>
    </div>

    <p v-if="currentDataset" class="dataset-desc">{{ currentDataset.description }}</p>

    <div class="content">
      <div class="left">
        <ImagePicker
          :images="sampleImages"
          :model-value="selectedImageId"
          @update:model-value="(v: string) => { selectedImageId = v; uploadedFile = null }"
          @upload="onUpload"
        />
        <p v-if="uploadedFile" class="hint">已选择本地图片：{{ uploadedFile.name }}</p>
      </div>

      <div class="right">
        <div v-if="!prediction && !predicting" class="placeholder">
          选择一张图片后点击「开始预测」查看分割结果
        </div>
        <div v-else-if="predicting" class="placeholder">正在推理，请稍候…</div>
        <template v-else-if="prediction">
          <ResultViewer :result="prediction" />
          <div class="distribution">
            <div class="dist-title">类别占比</div>
            <div
              v-for="d in prediction.distribution"
              :key="d.classId"
              class="dist-row"
            >
              <span class="swatch" :style="{ backgroundColor: d.color }"></span>
              <span class="dist-name">{{ d.className }}</span>
              <div class="dist-bar-wrap">
                <div class="dist-bar" :style="{ width: (d.ratio * 100).toFixed(1) + '%' }"></div>
              </div>
              <span class="dist-pct">{{ (d.ratio * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <ClassLegend v-if="currentDataset" :classes="currentDataset.classes" />
  </section>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 1.2rem;
}
.toolbar {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  flex-wrap: wrap;
}
.predict-btn {
  padding: 0.55rem 1.4rem;
  border-radius: 8px;
  border: none;
  background: var(--seg-accent);
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
}
.predict-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.dataset-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--seg-text-muted);
}
.content {
  display: grid;
  grid-template-columns: minmax(240px, 320px) 1fr;
  gap: 1.2rem;
  align-items: start;
}
.left {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.hint {
  font-size: 0.78rem;
  color: var(--seg-text-muted);
  margin: 0;
}
.right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  min-height: 260px;
}
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 260px;
  border: 1px dashed var(--seg-border);
  border-radius: 10px;
  color: var(--seg-text-muted);
  font-size: 0.9rem;
}
.distribution {
  border: 1px solid var(--seg-border);
  border-radius: 10px;
  padding: 0.85rem 1rem;
  background: var(--seg-surface);
}
.dist-title {
  font-size: 0.85rem;
  color: var(--seg-text-muted);
  margin-bottom: 0.6rem;
}
.dist-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
  font-size: 0.8rem;
}
.swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}
.dist-name {
  width: 130px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dist-bar-wrap {
  flex: 1;
  height: 10px;
  background: var(--seg-surface-2);
  border-radius: 5px;
  overflow: hidden;
}
.dist-bar {
  height: 100%;
  background: var(--seg-accent);
  opacity: 0.75;
}
.dist-pct {
  width: 48px;
  text-align: right;
  color: var(--seg-text-muted);
}
@media (max-width: 760px) {
  .content {
    grid-template-columns: 1fr;
  }
}
</style>
