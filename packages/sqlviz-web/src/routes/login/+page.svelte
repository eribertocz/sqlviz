<script lang="ts">
    import { goto } from '$app/navigation';

    let password = $state('');
    let error = $state<string | null>(null);
    let submitting = $state(false);

    async function submit(e: SubmitEvent) {
        e.preventDefault();
        if (submitting) return;
        submitting = true;
        error = null;

        try {
            const resp = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password }),
            });
            if (resp.ok) {
                await goto('/');
            } else {
                error = 'Invalid password';
                password = '';
            }
        } catch {
            error = 'Could not reach the server. Is it running?';
        } finally {
            submitting = false;
        }
    }
</script>

<svelte:head>
    <title>Sign in — SQLviz</title>
</svelte:head>

<div class="auth-page">
    <div class="auth-card">
        <div class="auth-logo">SQLviz</div>

        <form class="auth-form" onsubmit={submit}>
            <label class="auth-label" for="pw">Password</label>
            <input
                id="pw"
                type="password"
                class="auth-input"
                bind:value={password}
                placeholder="Admin password"
                autocomplete="current-password"
                disabled={submitting}
                autofocus
            />

            {#if error}
                <div class="auth-error" role="alert">{error}</div>
            {/if}

            <button
                type="submit"
                class="auth-btn"
                disabled={submitting || password.length === 0}
            >
                {submitting ? 'Signing in…' : 'Sign in'}
            </button>
        </form>
    </div>
</div>

<style>
    .auth-page {
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--sqlviz-bg);
        padding: 1.5rem;
    }

    .auth-card {
        width: 100%;
        max-width: 360px;
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius-lg);
        padding: 2rem 2rem 1.75rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .auth-logo {
        font-size: 1.375rem;
        font-weight: 800;
        color: var(--sqlviz-primary);
        letter-spacing: -0.03em;
        text-align: center;
    }

    .auth-form {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .auth-label {
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
    }

    .auth-input {
        width: 100%;
        height: 40px;
        padding: 0 0.875rem;
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text);
        font-size: 0.9375rem;
        font-family: var(--sqlviz-font-sans);
        outline: none;
        box-sizing: border-box;
        transition: border-color 0.15s;
    }

    .auth-input:focus {
        border-color: var(--sqlviz-primary);
    }

    .auth-input:disabled {
        opacity: 0.5;
    }

    .auth-error {
        font-size: 0.8125rem;
        color: var(--sqlviz-negative);
        padding: 0.375rem 0.625rem;
        background: color-mix(in srgb, var(--sqlviz-negative) 10%, transparent);
        border-radius: var(--sqlviz-radius);
    }

    .auth-btn {
        height: 40px;
        padding: 0 1rem;
        background: var(--sqlviz-primary);
        color: #fff;
        border: none;
        border-radius: var(--sqlviz-radius);
        font-size: 0.9375rem;
        font-weight: 600;
        cursor: pointer;
        transition: opacity 0.15s;
        margin-top: 0.25rem;
    }

    .auth-btn:hover:not(:disabled) {
        opacity: 0.85;
    }

    .auth-btn:disabled {
        opacity: 0.45;
        cursor: not-allowed;
    }
</style>
