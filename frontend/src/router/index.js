import { createRouter, createWebHistory } from "vue-router";

import Welcome from "../views/Welcome.vue";
import Register from "../views/Register.vue";
import ThemeSelection from "../views/ThemeSelection.vue";
import UploadPhoto from "../views/UploadPhoto.vue";
import Loading from "../views/Loading.vue";
import Result from "../views/Result.vue";
import PublicGallery from "../views/PublicGallery.vue";
import Setting from "../views/Setting.vue";
import ThemeSetting from "../views/ThemeSetting.vue";

const routes = [
  { path: "/", name: "Welcome", component: Welcome },
  { path: "/register", name: "Register", component: Register },
  { path: "/themes", name: "ThemeSelection", component: ThemeSelection },
  { path: "/upload", name: "UploadPhoto", component: UploadPhoto },
  { path: "/loading", name: "Loading", component: Loading },
  { path: "/result", name: "Result", component: Result },
  { path: "/public-gallery", name: "PublicGallery", component: PublicGallery },
  { path: "/setting", name: "Setting", component: Setting },
  { path: "/theme-setting", name: "ThemeSetting", component: ThemeSetting },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
