import { defineConfig } from 'vite';

// Windows can hold a Vite dependency cache after a process exits. Give every
// dev-server process its own ignored cache, so a locked old cache never blocks
// the next `npm run dev`.
export default defineConfig({
  cacheDir: `node_modules/.kanjiai-vite-cache-${process.pid}`,
});
