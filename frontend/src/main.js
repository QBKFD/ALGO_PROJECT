import "./assets/main.css";
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import { wsService } from "./utils/websocketService";

const app = createApp(App);

// COMMENT OUT WebSocket for now (add later for live data)
// wsService.connect("ws://localhost:8001/ws/live-data/XAUUSD");
// app.config.globalProperties.$wss = wsService;

app
  .use(router)
  .use(createPinia())
  .mount("#app");