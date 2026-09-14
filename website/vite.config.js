import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Standalone marketing site for the DaranX brand.
// Runs on a separate port from the accounting frontend (5173).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
  },
});
