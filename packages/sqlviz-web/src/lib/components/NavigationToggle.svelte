<script lang="ts">
    import PanelLeftCloseIcon from '@lucide/svelte/icons/panel-left-close';
    import PanelLeftOpenIcon from '@lucide/svelte/icons/panel-left-open';
    import sqlvizIcon from '$lib/assets/sqlviz-icon.svg';

    let { expanded, controls = 'workspace-navigation', onclick }: {
        expanded: boolean;
        controls?: string;
        onclick: () => void;
    } = $props();
</script>

<button
    type="button"
    class="navigation-toggle"
    data-navigation-trigger
    data-navigation-controls={controls}
    aria-label={expanded ? 'Hide navigation' : 'Show navigation'}
    aria-expanded={expanded}
    aria-controls={controls}
    title={`${expanded ? 'Hide' : 'Show'} navigation (Ctrl/Cmd+B)`}
    {onclick}
>
    <span class="brand-mark" aria-hidden="true">
        <img src={sqlvizIcon} alt="" width="22" height="22" />
    </span>
    <span class="navigation-action" aria-hidden="true">
        {#if expanded}
            <PanelLeftCloseIcon size={20} strokeWidth={1.75} />
        {:else}
            <PanelLeftOpenIcon size={20} strokeWidth={1.75} />
        {/if}
    </span>
</button>

<style>
    .navigation-toggle {
        display: inline-grid;
        place-items: center;
        width: 36px;
        padding: 0;
        height: 36px;
        flex-shrink: 0;
        color: var(--sqlviz-primary);
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        cursor: pointer;
        transition: background 120ms;
    }
    .navigation-toggle img { display: block; }
    .brand-mark, .navigation-action {
        grid-area: 1 / 1;
        display: grid;
        place-items: center;
        pointer-events: none;
        transition: opacity 120ms ease;
    }
    .navigation-action { opacity: 0; }
    .navigation-toggle:focus-visible .brand-mark { opacity: 0; }
    .navigation-toggle:focus-visible .navigation-action { opacity: 1; }
    @media (hover: hover) and (pointer: fine) {
        .navigation-toggle:hover .brand-mark { opacity: 0; }
        .navigation-toggle:hover .navigation-action { opacity: 1; }
    }
    @media (hover: none), (pointer: coarse) {
        .brand-mark { opacity: 0; }
        .navigation-action { opacity: 1; }
    }
    .navigation-toggle:hover {
        background: var(--sqlviz-bg-base);
    }
    .navigation-toggle[aria-expanded='true'] {
        background: color-mix(in srgb, var(--sqlviz-primary) 8%, transparent);
    }
    .navigation-toggle:focus-visible {
        outline: 2px solid var(--sqlviz-primary);
        outline-offset: 2px;
    }
    @media (max-width: 600px) {
        .navigation-toggle { width: 44px; height: 44px; }
    }
    @media (prefers-reduced-motion: reduce) {
        .navigation-toggle, .brand-mark, .navigation-action { transition: none; }
    }
</style>
