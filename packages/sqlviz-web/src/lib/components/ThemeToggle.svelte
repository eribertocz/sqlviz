<script lang="ts">
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import SunIcon from '@lucide/svelte/icons/sun';
    import MoonIcon from '@lucide/svelte/icons/moon';

    const dark = $derived(uiStore.theme === 'dark');
</script>

<button
    class="theme-switch"
    role="switch"
    aria-checked={dark}
    aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    title={dark ? 'Light mode' : 'Dark mode'}
    onclick={uiStore.toggleTheme}
>
    <span class="track">
        <SunIcon class="tt-ic tt-sun" size={11} />
        <MoonIcon class="tt-ic tt-moon" size={11} />
        <span class="knob" class:dark>
            {#if dark}<MoonIcon size={11} />{:else}<SunIcon size={11} />{/if}
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
</style>
