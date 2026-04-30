import { defineConfig } from "vite";

export default defineConfig({
  resolve: {
    // Allow template strings in plain JS components during this early scaffold stage.
    alias: {
      vue: "vue/dist/vue.esm-bundler.js",
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
  },
});
