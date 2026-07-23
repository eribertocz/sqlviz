<script lang="ts">
    import * as Dialog from '$lib/components/ui/dialog/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import { apiPost } from '$lib/api';
    import CheckIcon from '@lucide/svelte/icons/check';
    import CopyIcon from '@lucide/svelte/icons/copy';

    let { open = $bindable(false), dashboardId, dashboardName }: {
        open?: boolean;
        dashboardId: string | null;
        dashboardName: string;
    } = $props();

    type ShareMode = 'private' | 'password' | 'public';

    let mode = $state<ShareMode>('public');
    let password = $state('');
    let link = $state('');
    let creating = $state(false);
    let error = $state('');
    let copied = $state(false);

    const modes: { value: ShareMode; label: string; hint: string }[] = [
        { value: 'private',  label: 'Private',            hint: 'Only you can access it' },
        { value: 'password', label: 'Password protected', hint: 'Link plus a password' },
        { value: 'public',   label: 'Public',             hint: 'Anyone with the link' },
    ];

    // Reset transient state each time the modal opens; changing mode/password
    // invalidates any previously generated link.
    $effect(() => {
        if (open) {
            mode = 'public';
            password = '';
            link = '';
            error = '';
            copied = false;
        }
    });

    function onModeChange(next: ShareMode) {
        mode = next;
        link = '';
        error = '';
        copied = false;
    }

    type ShareResponse = { token: string; mode: string };

    async function generate() {
        if (!dashboardId || creating) return;
        if (mode === 'password' && !password.trim()) {
            error = 'Enter a password first.';
            return;
        }
        creating = true;
        error = '';
        try {
            const body = mode === 'password'
                ? { mode, password }
                : { mode };
            const resp = await apiPost<ShareResponse>(
                `/api/v1/dashboards/${dashboardId}/share`,
                body,
            );
            link = `${window.location.origin}/view/${resp.token}`;
        } catch (e) {
            error = e instanceof Error ? e.message : 'Could not create the share link.';
        } finally {
            creating = false;
        }
    }

    async function copy() {
        if (!link) return;
        try {
            await navigator.clipboard.writeText(link);
            copied = true;
            setTimeout(() => (copied = false), 1800);
        } catch {
            error = 'Could not copy to the clipboard.';
        }
    }
</script>

<Dialog.Root bind:open>
    <Dialog.Content class="sm:max-w-md">
        <Dialog.Header>
            <Dialog.Title>Share dashboard</Dialog.Title>
            <Dialog.Description>
                Choose who can access "{dashboardName}" and share a link.
            </Dialog.Description>
        </Dialog.Header>

        <fieldset class="share-modes">
            {#each modes as m (m.value)}
                <label class="share-mode" class:selected={mode === m.value}>
                    <input
                        type="radio"
                        name="share-mode"
                        value={m.value}
                        checked={mode === m.value}
                        onchange={() => onModeChange(m.value)}
                    />
                    <span class="radio-dot" aria-hidden="true"></span>
                    <span class="mode-text">
                        <span class="mode-label">{m.label}</span>
                        <span class="mode-hint">{m.hint}</span>
                    </span>
                </label>

                {#if m.value === 'password' && mode === 'password'}
                    <Input
                        type="password"
                        class="mt-1 h-9 text-sm"
                        placeholder="Dashboard password"
                        bind:value={password}
                        autocomplete="new-password"
                    />
                {/if}
            {/each}
        </fieldset>

        {#if link}
            <div class="link-row">
                <input class="link-input" readonly value={link} aria-label="Share link" />
                <button class="copy-btn" onclick={copy} aria-label="Copy link">
                    {#if copied}<CheckIcon class="size-4" />{:else}<CopyIcon class="size-4" />{/if}
                    {copied ? 'Copied' : 'Copy'}
                </button>
            </div>
        {/if}

        {#if error}
            <p class="share-error" role="alert">{error}</p>
        {/if}

        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (open = false)}>Close</Button>
            <Button size="sm" onclick={generate} disabled={creating || !dashboardId}>
                {creating ? 'Creating…' : link ? 'Regenerate link' : 'Create link'}
            </Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<style>
    .share-modes {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        border: none;
        margin: 0;
        padding: 0;
    }

    .share-mode {
        display: flex;
        align-items: flex-start;
        gap: 0.625rem;
        padding: 0.625rem 0.75rem;
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        transition: border-color 0.12s, background 0.12s;
    }
    .share-mode:hover { border-color: var(--sqlviz-primary); }
    .share-mode.selected {
        border-color: var(--sqlviz-primary);
        background: color-mix(in srgb, var(--sqlviz-primary) 8%, transparent);
    }

    /* Native radio hidden; a custom dot renders the state. */
    .share-mode input {
        position: absolute;
        opacity: 0;
        width: 0;
        height: 0;
    }

    .radio-dot {
        flex-shrink: 0;
        width: 16px;
        height: 16px;
        margin-top: 0.125rem;
        border: 2px solid var(--sqlviz-border);
        border-radius: 50%;
        transition: border-color 0.12s;
    }
    .share-mode.selected .radio-dot {
        border-color: var(--sqlviz-primary);
        background:
            radial-gradient(circle, var(--sqlviz-primary) 0 4px, transparent 5px);
    }

    .mode-text { display: flex; flex-direction: column; gap: 0.125rem; }
    .mode-label { font-size: 0.8125rem; font-weight: 600; color: var(--sqlviz-text); }
    .mode-hint { font-size: 0.75rem; color: var(--sqlviz-text-muted); }

    .link-row { display: flex; align-items: center; gap: 0.5rem; margin-top: 0.25rem; }
    .link-input {
        flex: 1;
        min-width: 0;
        height: 36px;
        padding: 0 0.625rem;
        font-size: 0.8125rem;
        font-family: var(--sqlviz-font-mono);
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        outline: none;
    }

    .copy-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        height: 36px;
        padding: 0 0.75rem;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        white-space: nowrap;
        transition: border-color 0.12s, color 0.12s;
    }
    .copy-btn:hover { border-color: var(--sqlviz-primary); color: var(--sqlviz-primary); }

    .share-error {
        margin: 0;
        font-size: 0.8125rem;
        color: var(--sqlviz-negative);
    }
</style>
