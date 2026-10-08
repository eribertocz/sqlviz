<script lang="ts">
    import { tick } from 'svelte';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';

    let { panelId, field, label, value, placeholder, compact = false, autofocus = false, onSaved, onCancel }: {
        panelId: string;
        field: 'title' | 'x_label' | 'y_label';
        label: string;
        value: string | null | undefined;
        placeholder: string;
        compact?: boolean;
        autofocus?: boolean;
        onSaved?: () => void;
        onCancel?: () => void;
    } = $props();
    const id = $props.id();
    let draft = $state('');
    let saving = $state(false);
    let error = $state<string | null>(null);
    let closing = false;
    let input = $state<HTMLInputElement | null>(null);
    $effect(() => { draft = value ?? ''; });
    $effect(() => { if (autofocus && input) { input.focus(); input.select(); } });

    async function save() {
        if (saving || closing) return;
        if (!error && draft === (value ?? '')) { finish(); return; }
        saving = true;
        error = null;
        try {
            error = await dashboardStore.setViewOverride(panelId, field, draft);
            await tick();
            if (!error) { draft = value ?? ''; finish(); }
        } catch {
            error = 'Could not save. Your text is kept; retry when ready.';
        } finally {
            saving = false;
        }
    }

    function finish() {
        if (onSaved) { closing = true; onSaved(); }
    }

    async function retry() {
        await save();
        input?.focus();
    }
</script>

<div class="presentation-input" class:compact>
    <label class="field-label" class:sr-only={compact || field === 'title'} for={id}>{label}</label>
    <Input {id} bind:ref={input} bind:value={draft} {placeholder} disabled={saving} class="text-foreground"
        aria-busy={saving} aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        onblur={save} onkeydown={(event) => {
            event.stopPropagation();
            if (event.key === 'Enter') { event.preventDefault(); void save(); }
            else if (event.key === 'Escape' && onCancel && !saving) {
                event.preventDefault();
                closing = true; // Restoring trigger focus must not save through blur.
                onCancel();
            }
        }} />
    {#if saving}
        <span class="save-status" role="status">Saving…</span>
    {:else if error}
        <div class="save-error">
            <span id={`${id}-error`} role="alert">{error}</span>
            <Button variant="ghost" size="sm" onclick={retry}>Retry</Button>
        </div>
    {/if}
</div>

<style>
    .presentation-input { display: grid; gap: 0.375rem; }
    .presentation-input.compact { width: 12rem; padding: 0.375rem; border-radius: 0.375rem; background: var(--background); box-shadow: 0 2px 10px rgb(0 0 0 / 0.12); }
    .field-label { font-size: 0.75rem; color: var(--muted-foreground); }
    .save-status { font-size: 0.75rem; color: var(--muted-foreground); }
    .save-error { display: flex; align-items: center; gap: 0.375rem; font-size: 0.75rem; color: var(--destructive); }
</style>
