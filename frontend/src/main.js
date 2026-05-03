import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import { i18n } from "./i18n/index.js";
import { router } from "./router/index.js";
import "./styles.css";

const app = createApp(App);

app.use(createPinia());
app.use(i18n);
app.use(router);
app.mount("#app");
