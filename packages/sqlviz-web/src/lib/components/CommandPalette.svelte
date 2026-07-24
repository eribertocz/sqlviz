<script lang="ts">
    import * as Command from '$lib/components/ui/command/index.js';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import { get } from 'svelte/store';
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import PlusIcon from '@lucide/svelte/icons/plus';
    import FolderPlusIcon from '@lucide/svelte/icons/folder-plus';
    import EyeIcon from '@lucide/svelte/icons/eye';
    import Code2Icon from '@lucide/svelte/icons/code-2';
    import SunIcon from '@lucide/svelte/icons/sun';
    import MoonIcon from '@lucide/svelte/icons/moon';
    import PanelLeftIcon from '@lucide/svelte/icons/panel-left';
    import Maximize2Icon from '@lucide/svelte/icons/maximize-2';

    let { open = $bindable(false) }: { open?: boolean } = $props();

    const folderName = (id: string | null) =>
        id ? (dashboardStore.folders.find(f => f.id === id)?.name ?? '') : '';

    function run(action: () => void) {
        open = false;
        // Defer so the dialog closes before we mutate app state.
        queueMicrotask(action);
    }

    function jump(id: string) {
        run(() => dashboardStore.loadDashboard(id));
    }
</script>

<Command.Dialog bind:open class="max-w-lg">
    <Command.Input placeholder="Jump to a dashboard or run a command…" />
    <Command.List>
        <Command.Empty>No results found.</Command.Empty>

        <Command.Group heading="Dashboards">
            {#each dashboardStore.allDashboards as d (d.id)}
                {@const Icon = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
                <Command.Item
                    value={`${d.name} ${folderName(d.folder_id)}`}
                    onSelect={() => jump(d.id)}
                >
                    <Icon class="size-4 opacity-70" />
                    <span>{d.name}</span>
                    {#if folderName(d.folder_id)}
                        <span class="ml-auto text-xs opacity-50">{folderName(d.folder_id)}</span>
                    {/if}
                </Command.Item>
            {/each}
        </Command.Group>

        <Command.Separator />

        <Command.Group heading="Actions">
            <Command.Item value="new dashboard create" onSelect={() => run(() => dashboardStore.createDashboard())}>
                <PlusIcon class="size-4 opacity-70" /> New dashboard
            </Command.Item>
            <Command.Item value="new group folder create" onSelect={() => run(() => dashboardStore.createFolder('New group'))}>
                <FolderPlusIcon class="size-4 opacity-70" /> New group
            </Command.Item>
            {#if get(editMode)}
                <Command.Item value="preview mode view" onSelect={() => run(() => editMode.set(false))}>
                    <EyeIcon class="size-4 opacity-70" /> Switch to Preview
                </Command.Item>
            {:else}
                <Command.Item value="edit mode sql" onSelect={() => run(() => editMode.set(true))}>
                    <Code2Icon class="size-4 opacity-70" /> Switch to Edit
                </Command.Item>
            {/if}
            <Command.Item value="focus zen mode fullscreen" onSelect={() => run(uiStore.toggleFocusMode)}>
                <Maximize2Icon class="size-4 opacity-70" /> Toggle focus mode
                <Command.Shortcut>⌘\</Command.Shortcut>
            </Command.Item>
            <Command.Item value="toggle sidebar rail" onSelect={() => run(uiStore.toggleSidebar)}>
                <PanelLeftIcon class="size-4 opacity-70" /> Toggle sidebar
                <Command.Shortcut>⌘B</Command.Shortcut>
            </Command.Item>
            <Command.Item value="theme dark light appearance" onSelect={() => run(uiStore.toggleTheme)}>
                {#if uiStore.theme === 'dark'}
                    <SunIcon class="size-4 opacity-70" /> Switch to light theme
                {:else}
                    <MoonIcon class="size-4 opacity-70" /> Switch to dark theme
                {/if}
            </Command.Item>
        </Command.Group>
    </Command.List>
</Command.Dialog>
