import { createRouter, createWebHistory } from "vue-router";

import Welcome from "../views/Welcome.vue";
import Register from "../views/Register.vue";
import ThemeSelection from "../views/ThemeSelection.vue";
import UploadPhoto from "../views/UploadPhoto.vue";
import Loading from "../views/Loading.vue";
import Result from "../views/Result.vue";

const routes = [
  { path: "/", name: "Welcome", component: Welcome },
  { path: "/register", name: "Register", component: Register },
  { path: "/themes", name: "ThemeSelection", component: ThemeSelection },
  { path: "/upload", name: "UploadPhoto", component: UploadPhoto },
  { path: "/loading", name: "Loading", component: Loading },
  { path: "/result", name: "Result", component: Result },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
