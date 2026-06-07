import { createRouter, createWebHistory } from "vue-router";
import HomePage from "../views/HomePage.vue";
import ConvertPage from "../views/ConvertPage.vue";
import WorkspacesPage from "../views/WorkspacesPage.vue";
import PromptsPage from "../views/PromptsPage.vue";

const routes = [
  { path: "/", name: "Home", component: HomePage },
  { path: "/convert", name: "Convert", component: ConvertPage },
  { path: "/workspaces", name: "Workspaces", component: WorkspacesPage },
  { path: "/prompts", name: "Prompts", component: PromptsPage },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
