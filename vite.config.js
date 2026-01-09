import { defineConfig } from 'vite';
import { resolve } from 'path';

const staticRoot = resolve(__dirname, 'static');

export default defineConfig({
  root: staticRoot,
  build: {
    outDir: resolve(__dirname, 'static/dist'),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        home: resolve(staticRoot, 'css/home.css'),
        analytics: resolve(staticRoot, 'css/analytics.css'),
        admin_dashboard: resolve(staticRoot, 'css/admin_dashboard.css'),
        gate_console: resolve(staticRoot, 'css/gate_console.css'),
        notifications: resolve(staticRoot, 'css/notifications.css'),
        'live-stats': resolve(staticRoot, 'js/live-stats.js')
      },
      output: {
        assetFileNames: 'assets/[name][extname]',
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js'
      }
    }
  }
});
