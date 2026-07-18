<script lang="ts">
    let { state = 'success' }: {
        state?: 'success' | 'warning' | 'degraded' | 'failed' | string;
    } = $props();
</script>

<span class="state-badge state-{state}">{state}</span>

<style>
    .state-badge {
        display: inline-block;
        padding: 0.0625rem 0.375rem;
        border-radius: 3px;
        font-size: 0.6875rem;
        font-weight: 600;
        white-space: nowrap;
    }
    .state-success  { background: rgba(34,197,94,0.15); color: var(--sqlviz-positive); }
    .state-warning  { background: rgba(234,179,8,0.15);  color: #d97706; }
    .state-degraded { background: rgba(239,68,68,0.15);  color: var(--sqlviz-negative); }
    .state-failed   { background: rgba(239,68,68,0.25);  color: var(--sqlviz-negative); }
</style>
