import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  css: {
    preprocessorOptions: {
      scss: {
        // UniApp's current Vite pipeline still calls Sass's legacy JS API.
        silenceDeprecations: ['legacy-js-api']
      }
    }
  }
})
