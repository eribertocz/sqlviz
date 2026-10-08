<script lang="ts">
    import { onMount, tick, type Snippet } from 'svelte';
    import { Dialog } from 'bits-ui';

    let { open, onOpenChange, children, id = 'workspace-navigation' }: {
        open: boolean;
        onOpenChange: (open: boolean) => void;
        children: Snippet<[() => void, () => void, boolean]>;
        id?: string;
    } = $props();

    let narrow = $state(false);
    let previouslyOpen = false;
    $effect(() => {
        if (previouslyOpen && !open) void restoreFocus();
        previouslyOpen = open;
    });

    onMount(() => {
        if (!window.matchMedia) return;
        const query = window.matchMedia('(max-width: 900px)');
        narrow = query.matches;
        const update = () => { narrow = query.matches; };
        query.addEventListener('change', update);
        return () => query.removeEventListener('change', update);
    });

    async function restoreFocus() {
        await tick();
        const trigger = document.querySelector<HTMLButtonElement>('[data-navigation-trigger]');
        if (trigger?.dataset.navigationControls === id || trigger?.getAttribute('aria-controls') === id) trigger.focus();
    }

    function changeOpen(value: boolean) {
        onOpenChange(value);
    }

    // A docked explorer stays open while organizing. On a narrow screen,
    // choosing a dashboard dismisses the modal so the result is immediately visible.
    function afterNavigate() {
        if (narrow) changeOpen(false);
    }
</script>

{#if narrow}
    <Dialog.Root {open} onOpenChange={changeOpen}>
        <Dialog.Portal>
            <Dialog.Overlay class="navigation-backdrop" />
            <Dialog.Content
                {id}
                class="navigation-drawer"
                onOpenAutoFocus={(event) => {
                    const search = document.getElementById(id)?.querySelector<HTMLInputElement>('input[type="search"]');
                    if (search) { event.preventDefault(); search.focus(); }
                }}
                onCloseAutoFocus={(event) => {
                    event.preventDefault();
                    void restoreFocus();
                }}
            >
                <Dialog.Title class="sr-only">Dashboard navigation</Dialog.Title>
                <Dialog.Description class="sr-only">Choose a dashboard or organize your workspace.</Dialog.Description>
                {@render children(afterNavigate, () => changeOpen(false), true)}
            </Dialog.Content>
        </Dialog.Portal>
    </Dialog.Root>
{:else if open}
    <aside {id} class="navigation-docked">
        {@render children(afterNavigate, () => changeOpen(false), false)}
    </aside>
{/if}

<style>
    .navigation-docked {
        width: 260px;
        flex-shrink: 0;
        min-height: 0;
        display: flex;
        flex-direction: column;
        border-right: 1px solid var(--sqlviz-hairline);
        animation: navigation-appear 140ms ease-out;
    }
    :global(.navigation-backdrop) {
        position: fixed;
        inset: 0;
        z-index: 39;
        background: rgb(0 0 0 / 28%);
    }
    :global(.navigation-drawer) {
        position: fixed;
        inset: 8px auto 8px 8px;
        z-index: 40;
        width: min(300px, calc(100vw - 32px));
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid var(--sqlviz-border);
        border-radius: 14px;
        background: var(--sqlviz-bg-surface);
        box-shadow: var(--sqlviz-shadow-drawer);
        outline: none;
        animation: navigation-appear 140ms ease-out;
    }
    @keyframes navigation-appear {
        from { opacity: 0; transform: translateX(-6px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @media (prefers-reduced-motion: reduce) {
        .navigation-docked, :global(.navigation-drawer) { animation: none; }
    }
</style>
