import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(rootDir, "src") } },
  test: {
    environment: "jsdom",
    globals: true,
    testTimeout: 15000,
    setupFiles: ["./src/test/setupTests.js"],
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include: ["src/features/auth/**/*.{js,jsx}", "src/features/fpo-access/**/*.{js,jsx}", "src/shared/api/**/*.js"],
    },
  },
});
