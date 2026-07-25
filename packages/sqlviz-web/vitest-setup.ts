// Defensive jsdom polyfills — ResizeObserver isn't implemented in jsdom,
// but components under EChartsRenderer use it.
if (typeof globalThis.ResizeObserver === 'undefined') {
    globalThis.ResizeObserver = class ResizeObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
    };
}

// jsdom implements neither the Pointer Capture API nor scrollIntoView. bits-ui
// menus (Select, Popover) call both while opening, so without these any test
// that opens one dies on `hasPointerCapture is not a function`.
if (typeof Element.prototype.hasPointerCapture === 'undefined') {
    Element.prototype.hasPointerCapture = () => false;
    Element.prototype.setPointerCapture = () => {};
    Element.prototype.releasePointerCapture = () => {};
}
if (typeof Element.prototype.scrollIntoView === 'undefined') {
    Element.prototype.scrollIntoView = () => {};
}

// jsdom has no PointerEvent either, so testing-library falls back to a plain
// Event whose `button` is undefined — and bits-ui only opens a menu for
// `button === 0`, so triggers silently stayed closed. Extending MouseEvent
// gives the mouse-button fields their real semantics.
if (typeof globalThis.PointerEvent === 'undefined') {
    globalThis.PointerEvent = class PointerEvent extends MouseEvent {
        readonly pointerId: number;
        readonly pointerType: string;
        constructor(type: string, params: PointerEventInit = {}) {
            super(type, params);
            this.pointerId = params.pointerId ?? 0;
            this.pointerType = params.pointerType ?? 'mouse';
        }
    } as unknown as typeof globalThis.PointerEvent;
}
