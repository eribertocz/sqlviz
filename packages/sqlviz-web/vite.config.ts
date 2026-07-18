import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [
        tailwindcss(),
        sveltekit(),
    ],
    test: {
        environment: 'jsdom',
        setupFiles: ['./vitest-setup.ts'],
    },
    // Under Vitest, force Vite to resolve packages (notably `svelte` itself)
    // via their browser entry point instead of the SSR/server one — Vitest
    // runs in Node but tests mount real client-side components.
    resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined,
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
