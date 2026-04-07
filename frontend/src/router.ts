import { createRouter, createWebHashHistory } from "vue-router"

import DashboardPage from "./views/DashboardPage.vue"
import HelpPage from "./views/HelpPage.vue"
import ProctoringPage from "./views/ProctoringPage.vue"
import PrintingPage from "./views/PrintingPage.vue"
import RoomsPage from "./views/RoomsPage.vue"
import SubjectsPage from "./views/SubjectsPage.vue"
import RegistrationPage from "./views/RegistrationPage.vue"

export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/dashboard", name: "dashboard", component: DashboardPage },
    { path: "/registration", name: "registration", component: RegistrationPage, meta: { keepAlive: true, preserveOnAppReset: true } },
    { path: "/subjects", name: "subjects", component: SubjectsPage },
    { path: "/proctoring", name: "proctoring", component: ProctoringPage },
    { path: "/rooms", name: "rooms", component: RoomsPage },
    { path: "/printing", name: "printing", component: PrintingPage, meta: { keepAlive: true } },
    { path: "/help", name: "help", component: HelpPage },
  ],
})

