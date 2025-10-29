import { createRouter, createWebHistory } from 'vue-router'
import MapView from "@/components/MapView.vue"
import HistoryView from "@/components/HistoryView.vue"
import HomePage from "@/components/HomePage.vue"
import AboutView from "@/components/AboutView.vue"
import ContactsView from "@/components/ContactsView.vue"
import UrbanGrowthView from "@/components/UrbanGrowthView.vue"
import InsideIthacaView from "@/components/InsideIthacaView.vue"
import AnalyticsView from "@/components/AnalyticsView.vue"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
    },
    {
      path: '/rent',
      name: 'rent',
      component: MapView,
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
    },
    {
      path: '/contact',
      name: 'contact',
      component: ContactsView,
    },
    {
      path: '/history',
      name: 'history',
      component: HistoryView,
    },
    {
      path: '/urbangrowth',
      name: 'urbangrowth',
      component: UrbanGrowthView,
    },
    {
      path: '/inside-ithaca',
      name: 'inside-ithaca',
      component: InsideIthacaView,
    },
    {
      path: '/analytics',
      name: 'analytics',
      component: AnalyticsView,
    },
  ],
})

export default router
