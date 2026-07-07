<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="brand">
        <span class="brand-mark">RS</span>
        <div class="brand-text">
          <h1>遥感影像语义分割可视化系统</h1>
          <p>UNet 遥感解译 · 数字工程课程设计</p>
        </div>
      </div>
      <nav class="app-nav">
        <RouterLink to="/predict">单图预测</RouterLink>
        <RouterLink to="/evaluate">测试集评估</RouterLink>
      </nav>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <footer class="app-footer">
      <span>已对接 FastAPI 后端 · BDCI2017 / DFC22 / WHDLD 真实 UNet 权重推理</span>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--seg-border);
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--seg-accent);
  color: #fff;
  font-weight: 700;
  font-size: 1.1rem;
}
.brand-text h1 {
  margin: 0;
  font-size: 1.2rem;
  line-height: 1.2;
}
.brand-text p {
  margin: 0.2rem 0 0;
  font-size: 0.8rem;
  color: var(--seg-text-muted);
}
.app-nav {
  display: flex;
  gap: 0.5rem;
}
.app-nav a {
  padding: 0.45rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  color: var(--seg-text-muted);
  border: 1px solid transparent;
}
.app-nav a:hover {
  background: var(--seg-surface-2);
}
.app-nav a.router-link-active {
  color: #fff;
  background: var(--seg-accent);
}
.app-footer {
  padding-top: 1rem;
  border-top: 1px solid var(--seg-border);
  font-size: 0.78rem;
  color: var(--seg-text-muted);
  text-align: center;
}
</style>
