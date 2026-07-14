import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Chat from '../views/Chat.vue'
import LearningPath from '../views/LearningPath.vue'
import Resources from '../views/Resources.vue'
import BuddyChat from '../views/BuddyChat.vue'
import CodePractice from '../views/CodePractice.vue'
import PythonSandbox from '../views/PythonSandbox.vue'
import Evaluation from '../views/Evaluation.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/chat', name: 'Chat', component: Chat },
  { path: '/learning-path', name: 'LearningPath', component: LearningPath },
  { path: '/resources', name: 'Resources', component: Resources },
  { path: '/buddy', name: 'BuddyChat', component: BuddyChat },
  { path: '/code-practice/:orm_id', name: 'CodePractice', component: CodePractice },
  { path: '/sandbox', name: 'PythonSandbox', component: PythonSandbox },
  { path: '/evaluation', name: 'Evaluation', component: Evaluation },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
