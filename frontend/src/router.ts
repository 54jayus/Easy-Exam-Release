import { createRouter, createWebHashHistory } from "vue-router"

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/dashboard", name: "dashboard", component: () => import("./views/DashboardPage.vue") },
    { path: "/registration", name: "registration", component: () => import("./views/RegistrationPage.vue"), meta: { keepAlive: true, preserveOnAppReset: true } },
    { path: "/subjects", name: "subjects", component: () => import("./views/SubjectsPage.vue") },
    { path: "/proctoring", name: "proctoring", component: () => import("./views/ProctoringPage.vue") },
    { path: "/rooms", name: "rooms", component: () => import("./views/RoomsPage.vue") },
    { path: "/printing", name: "printing", component: () => import("./views/PrintingPage.vue"), meta: { keepAlive: true } },
    { path: "/help", name: "help", component: () => import("./views/HelpPage.vue"), meta: { keepAlive: true } },
  ],
})

