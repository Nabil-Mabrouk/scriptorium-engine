import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '@/pages/Dashboard.vue';
import ProjectDetailPage from '@/pages/ProjectDetailPage.vue';

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
  },
  {
    path: '/projects/:id', // A dynamic route for a single project
    name: 'ProjectDetail',
    component: ProjectDetailPage,
    props: true, // Pass route params as component props
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;