import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import "element-plus/dist/index.css";
import "./styles.css";
import App from "./App.vue";
import { router } from "./router";
import { useLicenseStore } from "./stores/license";
import { createLogger } from "./lib/logger";

const logger = createLogger("renderer");

function safeJson(value: unknown): string {
  try {
    return JSON.stringify(value);
  } catch {
    return '"[无法序列化]"';
  }
}

function forwardConsole() {
  const original = {
    log: console.log.bind(console),
    info: console.info.bind(console),
    warn: console.warn.bind(console),
    error: console.error.bind(console),
    debug: console.debug ? console.debug.bind(console) : console.log.bind(console),
  };

  const forward = (level: "debug" | "info" | "warn" | "error", args: unknown[]) => {
    if (!window.electron?.ipcRenderer?.send) return;
    try {
      const msg = args.map((a) => (typeof a === "string" ? a : safeJson(a))).join(" ");
      window.electron.ipcRenderer.send("renderer-log", { level, scope: "console", message: msg });
    } catch {}
  };

  console.log = (...args: unknown[]) => {
    forward("info", args);
    original.log(...(args as any[]));
  };
  console.info = (...args: unknown[]) => {
    forward("info", args);
    original.info(...(args as any[]));
  };
  console.warn = (...args: unknown[]) => {
    forward("warn", args);
    original.warn(...(args as any[]));
  };
  console.error = (...args: unknown[]) => {
    forward("error", args);
    original.error(...(args as any[]));
  };
  console.debug = (...args: unknown[]) => {
    forward("debug", args);
    original.debug(...(args as any[]));
  };
}

forwardConsole();

window.addEventListener("error", (event) => {
  try {
    logger.error("窗口脚本异常", {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: (event.error as any)?.stack,
    });
  } catch {}
});

window.addEventListener("unhandledrejection", (event) => {
  try {
    const reason: any = (event as any).reason;
    logger.error("未处理的 Promise 拒绝", {
      reason: typeof reason === "string" ? reason : reason?.message ?? safeJson(reason),
      stack: reason?.stack,
    });
  } catch {}
});

const app = createApp(App);

const pinia = createPinia();
app.use(pinia);
app.use(router);
app.use(ElementPlus, {
  locale: zhCn,
});

const licenseStore = useLicenseStore(pinia);

router.beforeEach(async (to, from, next) => {
  if (!licenseStore.checked) {
    await licenseStore.refreshStatus();
  }
  if (!licenseStore.valid && to.path !== "/registration") {
    if (to.path === "/registration") {
      next();
      return;
    }
    next({ path: "/registration", replace: true });
    return;
  }
  next();
});

app.mount("#app");
