<script lang="ts">
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import SunIcon from '@lucide/svelte/icons/sun';
    import MoonIcon from '@lucide/svelte/icons/moon';

    // `compact` renders a smaller switch that fits the 44px collapsed rail.
    let { compact = false }: { compact?: boolean } = $props();

    const dark = $derived(uiStore.theme === 'dark');
    const ic = $derived(compact ? 9 : 11);
</script>

<button
    class="theme-switch"
    class:compact
    role="switch"
    aria-checked={dark}
    aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    title={dark ? 'Light mode' : 'Dark mode'}
    onclick={uiStore.toggleTheme}
>
    <span class="track">
        <SunIcon class="tt-ic tt-sun" size={ic} />
        <MoonIcon class="tt-ic tt-moon" size={ic} />
        <span class="knob" class:dark>
            {#if dark}<MoonIcon size={ic} />{:else}<SunIcon size={ic} />{/if}
        </span>
    </span>
</button>

<style>
    .theme-switch {
        display: inline-flex;
        padding: 0;
        border: none;
        background: none;
        cursor: pointer;
    }

    .track {
        position: relative;
        width: 44px;
        height: 24px;
        border-radius: 100px;
        background: var(--sqlviz-bg-base);
        border: 1px solid var(--sqlviz-border);
        transition: background 0.2s ease, border-color 0.2s ease;
    }
    .theme-switch:hover .track { border-color: var(--sqlviz-primary); }

    /* Faint context icons behind the knob (rendered by child lucide
       components, so they need :global to be targeted). */
    .track :global(.tt-ic) {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        color: var(--sqlviz-text-muted);
        opacity: 0.45;
    }
    .track :global(.tt-sun) { left: 5px; }
    .track :global(.tt-moon) { right: 5px; }

    .knob {
        position: absolute;
        top: 2px;
        left: 2px;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: var(--sqlviz-bg-surface);
        color: var(--sqlviz-primary);
        box-shadow: var(--sqlviz-shadow-card);
        transition: transform 0.2s ease;
    }
    .knob.dark { transform: translateX(20px); }

    /* ── Compact (collapsed rail) ─────────────────────────────── */
    .theme-switch.compact .track { width: 34px; height: 20px; }
    .theme-switch.compact .knob { width: 14px; height: 14px; }
    .theme-switch.compact .knob.dark { transform: translateX(14px); }
    .theme-switch.compact .track :global(.tt-sun) { left: 4px; }
    .theme-switch.compact .track :global(.tt-moon) { right: 4px; }
</style>
