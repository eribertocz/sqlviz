// Defensive jsdom polyfills — ResizeObserver isn't implemented in jsdom,
// but components under EChartsRenderer use it.
if (typeof globalThis.ResizeObserver === 'undefined') {
    globalThis.ResizeObserver = class ResizeObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
    };
}
