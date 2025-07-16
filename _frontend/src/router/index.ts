import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '@/pages/Dashboard.vue';
import ProjectDetail from '@/pages/ProjectDetail.vue';

const routes = [
  { path: '/', component: Dashboard },
  { path: '/projects/:id', component: ProjectDetail, props: true },
//   { path: '/parts/:id', component: PartDetail, props: true },
// { path: '/chapters/:id', component: ChapterDetail, props: true },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});