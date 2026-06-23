import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import LearningPath from '../views/LearningPath.vue'
import Resources from '../views/Resources.vue'
import BuddyChat from '../views/BuddyChat.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/chat', name: 'Chat', component: Chat },
  { path: '/learning-path', name: 'LearningPath', component: LearningPath },
  { path: '/resources', name: 'Resources', component: Resources },
  { path: '/buddy', name: 'BuddyChat', component: BuddyChat },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
