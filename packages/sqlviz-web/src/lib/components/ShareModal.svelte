<script lang="ts">
    import * as Dialog from '$lib/components/ui/dialog/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import { apiPost } from '$lib/api';
    import CheckIcon from '@lucide/svelte/icons/check';
    import CopyIcon from '@lucide/svelte/icons/copy';
    import EyeIcon from '@lucide/svelte/icons/eye';
    import EyeOffIcon from '@lucide/svelte/icons/eye-off';
    import RefreshIcon from '@lucide/svelte/icons/refresh-cw';

    let { open = $bindable(false), dashboardId, dashboardName }: {
        open?: boolean;
        dashboardId: string | null;
        dashboardName: string;
    } = $props();

    type ShareMode = 'private' | 'password' | 'public';
    type Scope = 'dashboard' | 'workspace';

    let scope = $state<Scope>('dashboard');
    let mode = $state<ShareMode>('public');
    let password = $state('');
    let showPassword = $state(false);

    // Strong, unique, readable password (no ambiguous 0/O/1/l/I).
    function generatePassword() {
        const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789';
        const n = 16;
        const buf = new Uint32Array(n);
        crypto.getRandomValues(buf);
        password = Array.from(buf, x => chars[x % chars.length]).join('');
        showPassword = true;
        invalidateLink();
    }
    let link = $state('');
    let creating = $state(false);
    let error = $state('');
    let copied = $state(false);

    const modes: { value: ShareMode; label: string; hint: string }[] = [
        { value: 'private',  label: 'Private (preview)',   hint: 'Only you — preview the viewer; nobody else can open it' },
        { value: 'password', label: 'Password protected', hint: 'Anyone on the network with the link + password' },
        { value: 'public',   label: 'Public',             hint: 'Anyone on the network with the link' },
    ];

    // Reset transient state each time the modal opens; changing mode/password
    // invalidates any previously generated link.
    $effect(() => {
        if (open) {
            scope = 'dashboard';
            mode = 'public';
            password = '';
            showPassword = false;
            link = '';
            error = '';
            copied = false;
        }
    });

    function invalidateLink() {
        link = '';
        error = '';
        copied = false;
    }
    function onScopeChange(next: Scope) { scope = next; invalidateLink(); }
    function onModeChange(next: ShareMode) { mode = next; invalidateLink(); }

    type ShareResponse = { token: string; mode: string };

    async function generate() {
        if (creating) return;
        if (scope === 'dashboard' && !dashboardId) return;
        if (mode === 'password' && !password.trim()) {
            error = 'Enter a password first.';
            return;
        }
        creating = true;
        error = '';
        try {
            const body = mode === 'password' ? { mode, password } : { mode };
            const resp = scope === 'workspace'
                ? await apiPost<ShareResponse>('/api/v1/workspace/share', body)
                : await apiPost<ShareResponse>(`/api/v1/dashboards/${dashboardId}/share`, body);
            link = scope === 'workspace'
                ? `${window.location.origin}/view/workspace/${resp.token}`
                : `${window.location.origin}/view/${resp.token}`;
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
            <Dialog.Title>Share</Dialog.Title>
            <Dialog.Description>
                Choose what to share and who can access it.
            </Dialog.Description>
        </Dialog.Header>

        <!-- Scope -->
        <fieldset class="share-modes">
            <label class="share-mode" class:selected={scope === 'dashboard'}>
                <input type="radio" name="share-scope" value="dashboard"
                    checked={scope === 'dashboard'} onchange={() => onScopeChange('dashboard')} />
                <span class="radio-dot" aria-hidden="true"></span>
                <span class="mode-text">
                    <span class="mode-label">This dashboard only</span>
                    <span class="mode-hint">Share only "{dashboardName}"</span>
                </span>
            </label>
            <label class="share-mode" class:selected={scope === 'workspace'}>
                <input type="radio" name="share-scope" value="workspace"
                    checked={scope === 'workspace'} onchange={() => onScopeChange('workspace')} />
                <span class="radio-dot" aria-hidden="true"></span>
                <span class="mode-text">
                    <span class="mode-label">All dashboards</span>
                    <span class="mode-hint">Share all dashboards with navigation</span>
                </span>
            </label>
        </fieldset>

        <div class="share-divider"></div>
        <p class="share-section">Visibility</p>

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
                    <div class="pw-row">
                        <input
                            class="pw-input"
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Password (type or generate)"
                            bind:value={password}
                            autocomplete="new-password"
                        />
                        <button type="button" class="pw-btn" onclick={() => (showPassword = !showPassword)}
                            title={showPassword ? 'Hide' : 'Show'} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                            {#if showPassword}<EyeOffIcon class="size-4" />{:else}<EyeIcon class="size-4" />{/if}
                        </button>
                        <button type="button" class="pw-btn pw-gen" onclick={generatePassword} title="Generate a strong password">
                            <RefreshIcon class="size-4" /> Generate
                        </button>
                    </div>
                    {#if password && showPassword}
                        <p class="pw-hint">Copy this password — you'll need to share it with viewers.</p>
                    {/if}
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
            <Button size="sm" onclick={generate} disabled={creating || (scope === 'dashboard' && !dashboardId)}>
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

    .share-divider {
        height: 1px;
        margin: 0.25rem 0;
        background: var(--sqlviz-hairline);
    }
    .share-section {
        margin: 0;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
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

    /* Password row: input + show toggle + generate */
    .pw-row { display: flex; align-items: center; gap: 0.375rem; margin-top: 0.25rem; }
    .pw-input {
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
    .pw-input:focus { border-color: var(--sqlviz-primary); }
    .pw-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        height: 36px;
        padding: 0 0.625rem;
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--sqlviz-text-muted);
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        white-space: nowrap;
        transition: border-color 0.12s, color 0.12s;
    }
    .pw-btn:hover { border-color: var(--sqlviz-primary); color: var(--sqlviz-text); }
    .pw-hint { margin: 0.375rem 0 0; font-size: 0.75rem; color: var(--sqlviz-text-muted); }
</style>
