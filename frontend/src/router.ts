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
    { path: "/dashboard", component: DashboardPage },
    { path: "/registration", component: RegistrationPage },
    { path: "/subjects", component: SubjectsPage },
    { path: "/proctoring", component: ProctoringPage },
    { path: "/rooms", component: RoomsPage },
    { path: "/printing", component: PrintingPage },
    { path: "/help", component: HelpPage },
  ],
})

