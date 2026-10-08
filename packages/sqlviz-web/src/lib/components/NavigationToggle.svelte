<script lang="ts">
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
    <img src={sqlvizIcon} alt="" width="22" height="22" />
</button>

<style>
    .navigation-toggle {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        padding: 0;
        height: 36px;
        flex-shrink: 0;
        color: var(--sqlviz-text-muted);
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px;
        cursor: pointer;
        transition: background 120ms, color 120ms;
    }
    .navigation-toggle img { display: block; }
    .navigation-toggle:hover {
        background: var(--sqlviz-bg-base);
        color: var(--sqlviz-text);
    }
    .navigation-toggle[aria-expanded='true'] {
        color: var(--sqlviz-primary);
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
        .navigation-toggle { transition: none; }
    }
</style>
