import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [
        tailwindcss(),
        sveltekit(),
    ],
    server: {
        // In dev, proxy /api/* to the FastAPI server so the SvelteKit
        // dev server and the Python server don't need CORS configuration.
        // In production, both are served from the same FastAPI origin.
        proxy: {
            '/api': 'http://localhost:4000',
            '/view': 'http://localhost:4000',
        },
    },
});
