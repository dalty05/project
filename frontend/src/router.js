import { createRouter, createWebHistory } from "vue-router";


const routes =[
  {
    path: "/",
    name: "PublicEvents",
    component: () => import("./views/PublicEvents.vue"), 
  },
  {
    path: "/login",
    name: "Login",
    component: () => import("./views/Login.vue"),
  },
  {
    path: "/admin",
    name: "AdminDashboard",
    component: () => import("./views/AdminDashboard.vue"),
    meta: { requiresAuth: true, role: "admin" }, // Protected Route
  },
  {
    path: "/host",
    name: "HostDashboard",
    component: () => import("./views/HostDashboard.vue"),
    meta: { requiresAuth: true, role: "host" }, // Protected Route
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// ROUTE GUARD: Checks permissions before changing pages
router.beforeEach((to, from, next) => {
// ROUTE GUARD
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("token");
  const user = JSON.parse(localStorage.getItem("user"));

  if (to.meta.requiresAuth) {
    if (!token || !user) {
      return next("/login");
    }

    // ✨ NEW: Block navigation if password change is required
    if (user.must_change_password === 1 && to.path !== "/login") {
      return next("/login");
    }

    if (to.meta.role && to.meta.role !== user.role) {
      return next("/"); 
    }
  }

  next();
});

  // Allow access
  next();
});

export default router;