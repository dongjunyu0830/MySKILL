import { createRouter, createWebHistory } from 'vue-router'
import PredictView from '../views/PredictView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/predict',
    },
    {
      path: '/predict',
      name: 'predict',
      component: PredictView,
    },
    {
      path: '/evaluate',
      name: 'evaluate',
      // 懒加载
      component: () => import('../views/EvaluateView.vue'),
    },
  ],
})

export default router
