import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

// https://vite.dev/config/
// base: './' makes the built app work when served from any subpath (e.g.
// https://<user>.github.io/<repo>/) as well as opened directly from disk —
// change to '/' only if you deploy to a domain root.
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
})
