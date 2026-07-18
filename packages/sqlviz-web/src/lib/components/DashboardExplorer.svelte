<script lang="ts">
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import type { DashboardInfo, FolderInfo } from '$lib/types';
    import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
    import * as Dialog from '$lib/components/ui/dialog/index.js';
    import { Skeleton } from '$lib/components/ui/skeleton/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import PlusIcon from '@lucide/svelte/icons/plus';
    import FolderPlusIcon from '@lucide/svelte/icons/folder-plus';
    import FolderIcon from '@lucide/svelte/icons/folder';
    import ChevronRightIcon from '@lucide/svelte/icons/chevron-right';
    import EllipsisIcon from '@lucide/svelte/icons/ellipsis-vertical';
    import PencilIcon from '@lucide/svelte/icons/pencil';
    import FileTextIcon from '@lucide/svelte/icons/file-text';
    import FolderInputIcon from '@lucide/svelte/icons/folder-input';
    import Trash2Icon from '@lucide/svelte/icons/trash-2';

    // Which folders are collapsed (expanded by default).
    let collapsed = $state<Record<string, boolean>>({});
    // Row whose context menu is open (also driven by right-click).
    let openMenuId = $state<string | null>(null);

    // Dialog state — one dialog reused for each action kind.
    let renameOpen = $state(false);
    let descOpen = $state(false);
    let deleteOpen = $state(false);
    let newFolderOpen = $state(false);
    let target = $state<DashboardInfo | null>(null);
    let fieldValue = $state('');

    const folders = $derived(dashboardStore.folders);
    const dashboards = $derived(dashboardStore.allDashboards);

    function inFolder(folderId: string): DashboardInfo[] {
        return dashboards.filter(d => d.folder_id === folderId);
    }
    const ungrouped = $derived(dashboards.filter(d => !d.folder_id));

    function toggleFolder(id: string) {
        collapsed = { ...collapsed, [id]: !collapsed[id] };
    }

    function openRename(d: DashboardInfo) { target = d; fieldValue = d.name; renameOpen = true; }
    function openDesc(d: DashboardInfo)   { target = d; fieldValue = d.description ?? ''; descOpen = true; }
    function openDelete(d: DashboardInfo) { target = d; deleteOpen = true; }

    function submitRename() {
        if (target) dashboardStore.renameDashboard(target.id, fieldValue);
        renameOpen = false;
    }
    function submitDesc() {
        if (target) dashboardStore.setDashboardDescription(target.id, fieldValue.trim());
        descOpen = false;
    }
    function confirmDelete() {
        if (target) dashboardStore.deleteDashboardById(target.id);
        deleteOpen = false;
    }
    function submitNewFolder() {
        if (fieldValue.trim()) dashboardStore.createFolder(fieldValue);
        newFolderOpen = false;
    }

    function newDashboard() { dashboardStore.createDashboard('New Dashboard', null); }
    function newGroup() { fieldValue = ''; newFolderOpen = true; }
</script>

{#snippet row(d: DashboardInfo, indented: boolean)}
    {@const IconCmp = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
    <div
        class="row"
        class:active={d.id === dashboardStore.dashboardId}
        class:indented
    >
        <button
            class="row-main"
            onclick={() => dashboardStore.loadDashboard(d.id)}
            oncontextmenu={(e) => { e.preventDefault(); openMenuId = d.id; }}
            title={d.description || d.name}
        >
            <span class="row-icon"><IconCmp size={14} /></span>
            <span class="row-name">{d.name}</span>
        </button>

        <DropdownMenu.Root
            open={openMenuId === d.id}
            onOpenChange={(o) => { openMenuId = o ? d.id : (openMenuId === d.id ? null : openMenuId); }}
        >
            <DropdownMenu.Trigger class="row-kebab" aria-label="Dashboard options">
                <EllipsisIcon size={14} />
            </DropdownMenu.Trigger>
            <DropdownMenu.Content align="start" class="w-48">
                <DropdownMenu.Item onSelect={() => openRename(d)}>
                    <PencilIcon class="size-4" /> Rename
                </DropdownMenu.Item>
                <DropdownMenu.Item onSelect={() => openDesc(d)}>
                    <FileTextIcon class="size-4" /> Edit description
                </DropdownMenu.Item>
                <DropdownMenu.Sub>
                    <DropdownMenu.SubTrigger>
                        <FolderInputIcon class="size-4" /> Move to group
                    </DropdownMenu.SubTrigger>
                    <DropdownMenu.SubContent class="w-44">
                        {#if d.folder_id}
                            <DropdownMenu.Item onSelect={() => dashboardStore.moveDashboardToFolder(d.id, null)}>
                                Ungrouped
                            </DropdownMenu.Item>
                        {/if}
                        {#each folders as f (f.id)}
                            {#if f.id !== d.folder_id}
                                <DropdownMenu.Item onSelect={() => dashboardStore.moveDashboardToFolder(d.id, f.id)}>
                                    {f.name}
                                </DropdownMenu.Item>
                            {/if}
                        {/each}
                        {#if folders.length === 0}
                            <DropdownMenu.Item disabled>No groups yet</DropdownMenu.Item>
                        {/if}
                    </DropdownMenu.SubContent>
                </DropdownMenu.Sub>
                <DropdownMenu.Separator />
                <DropdownMenu.Item variant="destructive" onSelect={() => openDelete(d)}>
                    <Trash2Icon class="size-4" /> Delete
                </DropdownMenu.Item>
            </DropdownMenu.Content>
        </DropdownMenu.Root>
    </div>
{/snippet}

<nav class="explorer" aria-label="Dashboard explorer">
    <div class="explorer-header">
        <span class="explorer-title">Explorer</span>
        <div class="explorer-actions">
            <button class="hbtn" onclick={newGroup} title="New group" aria-label="New group">
                <FolderPlusIcon size={15} />
            </button>
            <button class="hbtn" onclick={newDashboard} title="New dashboard" aria-label="New dashboard">
                <PlusIcon size={16} />
            </button>
        </div>
    </div>

    <div class="explorer-body">
        {#if dashboardStore.dashboardsLoading}
            {#each Array(5) as _, i (i)}
                <div class="skeleton-row">
                    <Skeleton class="size-4 rounded" />
                    <Skeleton class="h-3.5 flex-1 rounded" />
                </div>
            {/each}
        {:else}
            {#each folders as f (f.id)}
                <button class="folder-header" onclick={() => toggleFolder(f.id)}>
                    <span class="chev" class:open={!collapsed[f.id]}><ChevronRightIcon size={14} /></span>
                    <FolderIcon size={14} />
                    <span class="folder-name">{f.name}</span>
                    <span class="folder-count">{inFolder(f.id).length}</span>
                </button>
                {#if !collapsed[f.id]}
                    {#each inFolder(f.id) as d (d.id)}
                        {@render row(d, true)}
                    {/each}
                {/if}
            {/each}

            {#each ungrouped as d (d.id)}
                {@render row(d, false)}
            {/each}

            {#if dashboards.length === 0}
                <p class="empty">No dashboards yet. Create one with the + button.</p>
            {/if}
        {/if}
    </div>

    <div class="explorer-footer">
        <Button variant="secondary" size="sm" class="w-full justify-start gap-2" onclick={newDashboard}>
            <PlusIcon class="size-4" /> New Dashboard
        </Button>
    </div>
</nav>

<!-- Rename dialog -->
<Dialog.Root bind:open={renameOpen}>
    <Dialog.Content class="sm:max-w-sm">
        <Dialog.Header>
            <Dialog.Title>Rename dashboard</Dialog.Title>
        </Dialog.Header>
        <Input bind:value={fieldValue} placeholder="Dashboard name"
            onkeydown={(e) => e.key === 'Enter' && submitRename()} />
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (renameOpen = false)}>Cancel</Button>
            <Button size="sm" onclick={submitRename}>Save</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<!-- Edit description dialog -->
<Dialog.Root bind:open={descOpen}>
    <Dialog.Content class="sm:max-w-md">
        <Dialog.Header>
            <Dialog.Title>Edit description</Dialog.Title>
            <Dialog.Description>Shown as a tooltip on the dashboard in the explorer.</Dialog.Description>
        </Dialog.Header>
        <Input bind:value={fieldValue} placeholder="Short description (optional)"
            onkeydown={(e) => e.key === 'Enter' && submitDesc()} />
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (descOpen = false)}>Cancel</Button>
            <Button size="sm" onclick={submitDesc}>Save</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<!-- Delete confirmation -->
<Dialog.Root bind:open={deleteOpen}>
    <Dialog.Content class="sm:max-w-sm">
        <Dialog.Header>
            <Dialog.Title>Delete dashboard</Dialog.Title>
            <Dialog.Description>
                "{target?.name}" and its panels will be permanently deleted. This cannot be undone.
            </Dialog.Description>
        </Dialog.Header>
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (deleteOpen = false)}>Cancel</Button>
            <Button variant="destructive" size="sm" onclick={confirmDelete}>Delete</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<!-- New group -->
<Dialog.Root bind:open={newFolderOpen}>
    <Dialog.Content class="sm:max-w-sm">
        <Dialog.Header>
            <Dialog.Title>New group</Dialog.Title>
        </Dialog.Header>
        <Input bind:value={fieldValue} placeholder="Group name"
            onkeydown={(e) => e.key === 'Enter' && submitNewFolder()} />
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (newFolderOpen = false)}>Cancel</Button>
            <Button size="sm" onclick={submitNewFolder}>Create</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<style>
    .explorer {
        width: 240px;
        flex-shrink: 0;
        background: var(--sqlviz-bg-surface);
        border-right: 1px solid var(--sqlviz-hairline);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .explorer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0.5rem 0.5rem 0.875rem;
        flex-shrink: 0;
    }

    .explorer-title {
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: var(--sqlviz-text-muted);
    }

    .explorer-actions { display: flex; gap: 0.125rem; }

    .hbtn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        transition: background 0.12s, color 0.12s;
    }
    .hbtn:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .explorer-body {
        flex: 1;
        overflow-y: auto;
        padding: 0 0.375rem 0.5rem;
    }

    .skeleton-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.4375rem 0.5rem;
    }

    .folder-header {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        width: 100%;
        padding: 0.375rem 0.5rem;
        margin-top: 0.125rem;
        background: none;
        border: none;
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        color: var(--sqlviz-text-muted);
        font-size: 0.75rem;
        font-weight: 600;
        text-align: left;
    }
    .folder-header:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }

    .chev { display: flex; transition: transform 0.15s; }
    .chev.open { transform: rotate(90deg); }

    .folder-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .folder-count { font-size: 0.6875rem; opacity: 0.7; font-weight: 500; }

    .row {
        display: flex;
        align-items: center;
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text-muted);
        transition: background 0.12s, color 0.12s;
    }
    .row:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .row.active { background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent); color: var(--sqlviz-primary); }
    .row.indented { margin-left: 0.75rem; }

    .row-main {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
        min-width: 0;
        padding: 0.4375rem 0.5rem;
        background: none;
        border: none;
        color: inherit;
        cursor: pointer;
        text-align: left;
    }

    .row-icon { flex-shrink: 0; display: flex; align-items: center; }
    .row-name {
        font-size: 0.8125rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.3;
    }

    :global(.row-kebab) {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 26px;
        margin-right: 0.25rem;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        opacity: 0;
        transition: opacity 0.12s, background 0.12s;
    }
    .row:hover :global(.row-kebab),
    .row.active :global(.row-kebab) { opacity: 1; }
    :global(.row-kebab:hover) { background: var(--sqlviz-border); color: var(--sqlviz-text); }

    .empty {
        padding: 0.75rem 0.5rem;
        font-size: 0.75rem;
        color: var(--sqlviz-text-muted);
        line-height: 1.4;
    }

    .explorer-footer {
        padding: 0.5rem;
        border-top: 1px solid var(--sqlviz-hairline);
        flex-shrink: 0;
    }
</style>
