<script lang="ts">
    import StateMessage from '$lib/components/shared/StateMessage.svelte';

    let { data }: { data: Record<string, unknown>[] } = $props();

    const columns = $derived(data.length > 0 ? Object.keys(data[0]) : []);

    function display(val: unknown): string {
        if (val == null) return '';
        if (typeof val === 'number') {
            return Number.isInteger(val)
                ? val.toLocaleString()
                : val.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
        return String(val);
    }
</script>

<div class="table-wrap">
    {#if data.length === 0}
        <StateMessage kind="empty" message="No data" />
    {:else}
        <table class="data-table">
            <thead>
                <tr>
                    {#each columns as col}
                        <th>{col.replace(/_/g, ' ')}</th>
                    {/each}
                </tr>
            </thead>
            <tbody>
                {#each data as row}
                    <tr>
                        {#each columns as col}
                            <td>{display(row[col])}</td>
                        {/each}
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
</div>

<style>
    .table-wrap {
        flex: 1;
        overflow: auto;
        padding: 0.5rem 0;
    }

    .data-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8125rem;
    }

    th, td {
        padding: 0.5rem 1rem;
        text-align: left;
        border-bottom: 1px solid var(--sqlviz-border);
        white-space: nowrap;
    }

    th {
        color: var(--sqlviz-text-muted);
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        position: sticky;
        top: 0;
        background: var(--sqlviz-bg-surface);
    }

    td {
        color: var(--sqlviz-text);
        font-family: var(--sqlviz-font-mono);
    }

    tbody tr:hover {
        background: color-mix(in srgb, var(--sqlviz-primary) 6%, transparent);
    }
</style>
