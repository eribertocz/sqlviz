<script lang="ts">
    import { uiStore } from '$lib/stores/uiStore.svelte';
</script>

{#if uiStore.toast}
    <div class="toast" role="status" aria-live="polite">{uiStore.toast}</div>
{/if}

<style>
    .toast {
        position: fixed;
        bottom: 1.25rem;
        left: 50%;
        transform: translateX(-50%);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-hairline);
        border-radius: var(--sqlviz-radius-lg);
        padding: 0.625rem 1.125rem;
        font-size: 0.875rem;
        color: var(--sqlviz-text);
        box-shadow: var(--sqlviz-shadow-drawer);
        z-index: 1000;
        white-space: nowrap;
        pointer-events: none;
    }
</style>
