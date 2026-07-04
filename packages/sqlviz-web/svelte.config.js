import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
    kit: {
        adapter: adapter({
            // Output directly to the path main.py expects:
            // Path(__file__).parent / "static" / "dist"
            pages: '../sqlviz-api/src/sqlviz_api/static/dist',
            assets: '../sqlviz-api/src/sqlviz_api/static/dist',
            // SPA fallback: FastAPI's app.frontend() handles this,
            // but we also set it here for completeness.
            fallback: 'index.html',
            precompress: false,
            strict: false,  // SPA mode: all routes rendered client-side via fallback
        }),
    },
};

export default config;
