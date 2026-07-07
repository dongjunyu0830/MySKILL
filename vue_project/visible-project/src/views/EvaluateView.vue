<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useAppStore } from '@/stores/app'
import DatasetSelector from '@/components/seg/DatasetSelector.vue'
import ModelSelector from '@/components/seg/ModelSelector.vue'
import MetricsPanel from '@/components/seg/MetricsPanel.vue'

const store = useAppStore()
const { datasets, models, currentDatasetId, currentModelId, currentDataset, evaluation, evaluating } =
  storeToRefs(store)

onMounted(async () => {
  await store.loadMeta()
})

function onSelectDataset(id: string) {
  store.setDataset(id)
}
function onSelectModel(id: string) {
  store.setModel(id)
}
async function onEvaluate() {
  await store.runEvaluate()
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
      <button class="eval-btn" :disabled="evaluating" @click="onEvaluate">
        {{ evaluating ? '评估中…' : '在测试集上评估' }}
      </button>
    </div>

    <p v-if="currentDataset" class="dataset-desc">
      当前：{{ currentDataset.name }}　模型：{{ store.currentModel?.name }}
    </p>

    <div class="result">
      <div v-if="!evaluation && !evaluating" class="placeholder">
        点击「在测试集上评估」查看 mIoU / Precision / Recall / F1 等指标
      </div>
      <div v-else-if="evaluating" class="placeholder">正在评估测试集，请稍候…</div>
      <MetricsPanel v-else-if="evaluation" :result="evaluation" />
    </div>
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
.eval-btn {
  padding: 0.55rem 1.4rem;
  border-radius: 8px;
  border: none;
  background: var(--seg-accent);
  color: #fff;
  font-size: 0.9rem;
  cursor: pointer;
}
.eval-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.dataset-desc {
  margin: 0;
  font-size: 0.85rem;
  color: var(--seg-text-muted);
}
.result {
  min-height: 220px;
}
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  border: 1px dashed var(--seg-border);
  border-radius: 10px;
  color: var(--seg-text-muted);
  font-size: 0.9rem;
}
</style>
