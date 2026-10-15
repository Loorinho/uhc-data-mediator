import { defineConfig } from 'vite'
import { devtools } from '@tanstack/devtools-vite'

import { tanstackStart } from '@tanstack/react-start/plugin/vite'

import viteReact from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import tsconfigPaths from 'vite-tsconfig-paths'

const config = defineConfig({
  plugins: [tsconfigPaths(), devtools(), tailwindcss(), tanstackStart(), viteReact()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    // File-system events don't cross the Docker bind-mount boundary,
    // so Vite must poll for changes made on the host.
    watch: {
      usePolling: true,
      interval: 300,
    },
    // HMR websocket must connect through the host-published port.
    hmr: {
      clientPort: 3000,
    },
  },
})

export default config
