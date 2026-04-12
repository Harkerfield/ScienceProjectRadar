import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import StepperControl from '../views/StepperControl.vue'
import RadarControl from '../views/RadarControl.vue'
import Settings from '../views/Settings.vue'
import DeviceTester from '../views/DeviceTester.vue'
import NotFound from '../views/NotFound.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { title: 'Dashboard' }
  },
  {
    path: '/stepper',
    name: 'StepperControl',
    component: StepperControl,
    meta: { title: 'Stepper Motor Control' }
  },
  {
    path: '/radar',
    name: 'RadarControl',
    component: RadarControl,
    meta: { title: 'Radar Control' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { title: 'Settings' }
  },
  {
    path: '/tester',
    name: 'DeviceTester',
    component: DeviceTester,
    meta: { title: 'Microcontroller Tester' }
  },
  {
    path: '/404',
    name: 'NotFound',
    component: NotFound,
    meta: { title: 'Page Not Found' }
  },
  {
    path: '/:catchAll(.*)',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Update document title
  document.title = to.meta.title ? `${to.meta.title} - Radar Control System` : 'Radar Control System'

  next()
})

export default router
