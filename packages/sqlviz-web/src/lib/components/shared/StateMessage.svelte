<script lang="ts">
    import { ArrowDown, CircleX, Loader2, TriangleAlert } from 'lucide-svelte';

    let { kind, message, hint }: {
        kind: 'loading' | 'empty' | 'error' | 'degraded';
        message: string;
        hint?: string;
    } = $props();

    const ICON: Record<typeof kind, typeof Loader2> = {
        loading:  Loader2,
        empty:    ArrowDown,
        error:    CircleX,
        degraded: TriangleAlert,
    };

    const StateIcon = $derived(ICON[kind]);
</script>

<div class="state-message state-{kind}" role={kind === 'error' ? 'alert' : 'status'}>
    <span class="state-icon" class:spinning={kind === 'loading'}>
        <StateIcon size={32} strokeWidth={1.75} />
    </span>
    <p class="state-text">{message}</p>
    {#if hint}
        <p class="state-hint">{hint}</p>
    {/if}
</div>

<style>
    .state-message {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        color: var(--sqlviz-text-muted);
        text-align: center;
    }

    .state-message.state-error { color: var(--sqlviz-negative); }
    .state-message.state-degraded { color: var(--sqlviz-neutral); }

    .state-icon {
        display: inline-flex;
        line-height: 1;
        opacity: 0.7;
    }

    .state-message.state-empty .state-icon { opacity: 0.2; }

    .state-icon.spinning {
        animation: state-spin 1.2s linear infinite;
        opacity: 1;
    }

    @keyframes state-spin { to { transform: rotate(360deg); } }

    .state-text {
        margin: 0;
        font-size: 0.9375rem;
    }

    .state-hint {
        margin: 0;
        font-size: 0.8125rem !important;
        opacity: 0.6;
    }
</style>
