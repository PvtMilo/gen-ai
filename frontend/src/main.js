import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";
import { useSeedDreamStore } from "./stores/seeddreamStore";

import "./style.css";

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);

useSeedDreamStore(pinia).hydrate();

app.mount("#app");
