<script lang="ts">
    import { Dialog } from 'bits-ui';
    import { runResolutionComplete, type SqlRunResolution } from '$lib/sql/sqlRunResolution';

    let { resolution, onChoose, onRemove, onConfirm, onCancel, error = null }: {
        resolution: SqlRunResolution | null;
        onChoose: (index: number, panelId: string | null | undefined) => void;
        onRemove: (panelId: string, remove: boolean) => void;
        onConfirm: () => void | Promise<void>;
        onCancel: () => void;
        error?: string | null;
    } = $props();
    const complete = $derived(resolution !== null && runResolutionComplete(resolution));
    const unmatched = $derived(resolution?.panels.filter(panel => !resolution?.choices.some(
        choice => choice.kind === 'keep' && choice.panel_id === panel.id,
    )) ?? []);
    const removedCount = $derived(resolution?.choices.filter(choice => choice.kind === 'remove').length ?? 0);
    function value(index: number) {
        const choice = resolution?.choices.find(item => item.kind !== 'remove' && item.statement_index === index);
        return choice?.kind === 'keep' ? `keep:${choice.panel_id}` : choice?.kind === 'create' ? 'new' : '';
    }
    function choose(index: number, selected: string) {
        onChoose(index, selected === '' ? undefined : selected === 'new' ? null : selected.slice(5));
    }
    function focusRun() {
        document.querySelector<HTMLButtonElement>('[data-sql-run-trigger]')?.focus();
    }
    async function confirm() {
        await onConfirm();
        // Closing starts Run, so its trigger is initially disabled. Restore focus
        // after completion, unless a failed preflight opened the dialog again.
        if (resolution === null) focusRun();
    }
</script>

<Dialog.Root open={resolution !== null} onOpenChange={open => { if (!open) onCancel(); }}>
    <Dialog.Portal>
        <Dialog.Overlay class="resolution-backdrop" />
        <Dialog.Content class="resolution-dialog"
            onOpenAutoFocus={event => {
                const first = document.querySelector<HTMLElement>('.resolution-dialog select, .resolution-dialog input');
                if (first) { event.preventDefault(); first.focus(); }
            }}
            onCloseAutoFocus={event => {
                event.preventDefault(); focusRun();
            }}>
            <header>
                <Dialog.Title class="resolution-title">Confirm query associations</Dialog.Title>
                <Dialog.Description class="resolution-description">
                    Keep each panel’s settings with the right query. Decide explicitly what to remove.
                </Dialog.Description>
            </header>
            {#if resolution}
                <div class="resolution-body">
                    {#each resolution.statements as statement, index (index)}
                        {@const selected = resolution.panels.find(panel => `keep:${panel.id}` === value(index))}
                        <section class="query-choice">
                            <label for={`query-panel-${index}`}>Query {index + 1}</label>
                            <pre aria-label={`SQL for query ${index + 1}`}><code>{statement.sql}</code></pre>
                            <select id={`query-panel-${index}`} value={value(index)} onchange={event => choose(index, event.currentTarget.value)}>
                                <option value="">Choose a panel…</option>
                                <option value="new">Create a new panel</option>
                                {#each resolution.panels as panel, panelIndex (panel.id)}
                                    <option value={`keep:${panel.id}`} disabled={resolution.choices.some(
                                        choice => choice.kind === 'keep' && choice.panel_id === panel.id && choice.statement_index !== index,
                                    )}>{panelIndex + 1} · {panel.label}</option>
                                {/each}
                            </select>
                            {#if selected}
                                <details><summary>Previous SQL · {selected.label}</summary><pre><code>{selected.sql}</code></pre></details>
                            {/if}
                        </section>
                    {/each}
                    {#if unmatched.length}
                        <div class="unassigned" role="status">
                            <strong>Panels without a query</strong>
                            <p>Assign them above or select removal. Nothing is removed automatically.</p>
                            {#each unmatched as panel (panel.id)}
                                <div class="removal-choice">
                                    <label class="removal-label">
                                        <input type="checkbox" aria-label={`Remove ${panel.label}`}
                                            checked={resolution.choices.some(choice => choice.kind === 'remove' && choice.panel_id === panel.id)}
                                            onchange={event => onRemove(panel.id, event.currentTarget.checked)} />
                                        <span>Remove <strong>{panel.label}</strong> from this dashboard</span>
                                    </label>
                                    <details><summary>Previous SQL · {panel.label}</summary><pre><code>{panel.sql}</code></pre></details>
                                </div>
                            {/each}
                            {#if removedCount}<p class="removal-warning">{removedCount} {removedCount === 1 ? 'panel and its settings will' : 'panels and their settings will'} be removed when you confirm.</p>{/if}
                        </div>
                    {/if}
                    {#if error}<p class="resolution-error" role="alert">{error}</p>{/if}
                </div>
            {/if}
            <footer>
                <button class="cancel" onclick={onCancel}>Cancel</button>
                <button class="confirm" disabled={!complete} onclick={confirm}>{removedCount ? 'Confirm removal & run' : 'Run dashboard'}</button>
            </footer>
        </Dialog.Content>
    </Dialog.Portal>
</Dialog.Root>

<style>
    :global(.resolution-backdrop) { position: fixed; inset: 0; background: #0008; z-index: 100; }
    :global(.resolution-dialog) {
        position: fixed; inset: 50% auto auto 50%; transform: translate(-50%, -50%);
        width: min(680px, calc(100vw - 32px)); max-height: min(760px, calc(100dvh - 32px));
        display: flex; flex-direction: column; z-index: 101; overflow: hidden;
        background: var(--sqlviz-bg-surface); color: var(--sqlviz-text);
        border: 1px solid var(--sqlviz-border); border-radius: 16px; box-shadow: 0 24px 80px #0003;
    }
    header { padding: 24px 24px 16px; }
    :global(.resolution-title) { font-size: 1.125rem; font-weight: 600; }
    :global(.resolution-description) { color: var(--sqlviz-text-muted); font-size: 0.8125rem; margin-top: 8px; }
    .resolution-body { padding: 0 24px 20px; overflow: auto; min-height: 0; }
    .query-choice { padding: 16px 0; border-bottom: 1px solid var(--sqlviz-hairline); }
    label { display: block; font-size: 0.8125rem; font-weight: 600; margin-bottom: 8px; }
    pre { margin: 0 0 12px; padding: 10px 12px; max-height: 100px; overflow: auto;
        background: var(--sqlviz-bg-base); border-radius: 8px; font-size: 0.75rem; white-space: pre-wrap; overflow-wrap: anywhere; }
    select { width: 100%; min-height: 40px; padding: 8px; border: 1px solid var(--sqlviz-border);
        border-radius: 8px; background: var(--sqlviz-bg-surface); color: var(--sqlviz-text); font-size: 0.8125rem; }
    select:focus-visible, input:focus-visible, button:focus-visible, summary:focus-visible { outline: 2px solid var(--sqlviz-primary); outline-offset: 2px; }
    details { margin-top: 12px; font-size: 0.75rem; color: var(--sqlviz-text-muted); }
    summary { cursor: pointer; margin-bottom: 8px; }
    .unassigned { margin-top: 16px; font-size: 0.8125rem; }
    .unassigned p { color: var(--sqlviz-text-muted); margin-top: 6px; }
    .removal-choice { padding: 12px 0; border-bottom: 1px solid var(--sqlviz-hairline); }
    .removal-label { display: flex; align-items: center; gap: 10px; margin: 0; min-height: 40px; font-weight: 400; cursor: pointer; }
    .removal-label input { flex: 0 0 auto; width: 18px; height: 18px; accent-color: var(--sqlviz-primary); }
    .unassigned .removal-warning { color: var(--sqlviz-negative); }
    .resolution-error { color: var(--sqlviz-negative); font-size: 0.8125rem; margin-top: 12px; }
    footer { display: flex; justify-content: flex-end; gap: 8px; padding: 16px 24px; border-top: 1px solid var(--sqlviz-hairline); }
    button { min-height: 40px; padding: 8px 16px; border-radius: 8px; font-size: 0.8125rem; cursor: pointer; }
    .cancel { background: transparent; color: var(--sqlviz-text); border: 1px solid var(--sqlviz-border); }
    .cancel:hover { background: var(--sqlviz-bg-base); }
    .confirm { background: var(--sqlviz-primary); color: var(--sqlviz-on-primary); border: 1px solid transparent; }
    .confirm:hover:not(:disabled) { background: var(--sqlviz-primary-hover); }
    .confirm:disabled { opacity: 0.45; cursor: not-allowed; }
    @media (max-width: 600px) { header, footer { padding: 16px; } .resolution-body { padding: 0 16px 16px; } select, button { min-height: 44px; } }
</style>
