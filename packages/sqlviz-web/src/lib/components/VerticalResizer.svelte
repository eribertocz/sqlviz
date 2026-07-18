<script lang="ts">
    let { onDrag, ariaLabel = 'Resize editor' }: {
        onDrag: (deltaY: number) => void;
        ariaLabel?: string;
    } = $props();

    let dragging = $state(false);

    function startDrag(e: PointerEvent) {
        dragging = true;
        (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    }

    function onPointerMove(e: PointerEvent) {
        if (!dragging) return;
        onDrag(e.movementY);
    }

    function endDrag() {
        dragging = false;
    }

    function handleKeydown(e: KeyboardEvent) {
        if (e.key === 'ArrowUp')   { e.preventDefault(); onDrag(-10); }
        if (e.key === 'ArrowDown') { e.preventDefault(); onDrag(10); }
    }
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<div
    class="resizer"
    class:dragging
    role="separator"
    aria-orientation="horizontal"
    aria-label={ariaLabel}
    tabindex="0"
    onpointerdown={startDrag}
    onpointermove={onPointerMove}
    onpointerup={endDrag}
    onpointercancel={endDrag}
    onkeydown={handleKeydown}
>
    <span class="grip" aria-hidden="true">
        <span></span>
        <span></span>
        <span></span>
    </span>
</div>

<style>
    .resizer {
        position: relative;
        height: 7px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: ns-resize;
        background: transparent;
        touch-action: none;
    }

    /* Always-visible divider line — subtle at rest, brighter on hover/drag */
    .resizer::before {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        top: 50%;
        height: 2px;
        transform: translateY(-50%);
        background: var(--sqlviz-border);
        transition: background 0.15s, height 0.15s;
    }

    .resizer:hover::before,
    .resizer:focus-visible::before {
        background: var(--sqlviz-primary-hover);
        height: 3px;
    }

    .resizer.dragging::before {
        background: var(--sqlviz-primary);
        height: 3px;
    }

    /* Grip indicator — three centered dots, hidden at rest, shown on hover/drag */
    .grip {
        position: relative;
        display: flex;
        align-items: center;
        gap: 3px;
        padding: 3px 8px;
        border-radius: var(--sqlviz-radius);
        opacity: 0;
        transition: opacity 0.15s, background 0.15s;
    }

    .grip span {
        width: 3px;
        height: 3px;
        border-radius: 50%;
        background: var(--sqlviz-text-muted);
        transition: background 0.15s;
    }

    .resizer:hover .grip,
    .resizer:focus-visible .grip {
        opacity: 1;
        background: var(--sqlviz-primary-hover);
    }

    .resizer.dragging .grip {
        opacity: 1;
        background: var(--sqlviz-primary);
    }

    .resizer:hover .grip span,
    .resizer:focus-visible .grip span,
    .resizer.dragging .grip span {
        background: #fff;
    }

    .resizer:focus-visible {
        outline: none;
    }
</style>
