<script lang="ts">
    import { resolveDashboardIcon } from '$lib/dashboardIcons';
    import { dashboardStore } from '$lib/stores/dashboardStore.svelte';
    import { uiStore } from '$lib/stores/uiStore.svelte';
    import { editMode } from '$lib/stores/editMode';
    import type { DashboardInfo } from '$lib/types';
    import { draggable, droppable, type DragDropState } from '@thisux/sveltednd';
    import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
    import * as Dialog from '$lib/components/ui/dialog/index.js';
    import * as Tooltip from '$lib/components/ui/tooltip/index.js';
    import { Skeleton } from '$lib/components/ui/skeleton/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Button } from '$lib/components/ui/button/index.js';
    import PlusIcon from '@lucide/svelte/icons/plus';
    import FolderPlusIcon from '@lucide/svelte/icons/folder-plus';
    import FolderIcon from '@lucide/svelte/icons/folder';
    import ChevronRightIcon from '@lucide/svelte/icons/chevron-right';
    import EllipsisIcon from '@lucide/svelte/icons/ellipsis-vertical';
    import PencilIcon from '@lucide/svelte/icons/pencil';
    import FolderInputIcon from '@lucide/svelte/icons/folder-input';
    import Trash2Icon from '@lucide/svelte/icons/trash-2';
    import GripVerticalIcon from '@lucide/svelte/icons/grip-vertical';
    import PanelLeftCloseIcon from '@lucide/svelte/icons/panel-left-close';
    import PanelLeftOpenIcon from '@lucide/svelte/icons/panel-left-open';

    let folderCollapsed = $state<Record<string, boolean>>({});
    let openMenuId = $state<string | null>(null);
    let openFolderMenuId = $state<string | null>(null);

    // Single edit dialog (name + description together).
    let editOpen = $state(false);
    let editName = $state('');
    let editDesc = $state('');
    let editTarget = $state<DashboardInfo | null>(null);

    let deleteOpen = $state(false);
    let deleteTarget = $state<DashboardInfo | null>(null);
    let deleteGroupOpen = $state(false);
    let deleteGroupTarget = $state<{ id: string; name: string } | null>(null);

    // Inline name editing (double-click / F2). One at a time.
    let inline = $state<{ kind: 'dash' | 'folder'; id: string } | null>(null);
    let inlineValue = $state('');

    // Inline creation (VSCode-style): a new folder or dashboard is named directly
    // in the tree with an input — no modal. `folderId` is the target parent
    // (null = root). Folders never nest, so folder creation is always at root.
    let creating = $state<{ kind: 'dash' | 'folder'; folderId: string | null } | null>(null);
    let creatingValue = $state('');
    let creatingError = $state('');

    const collapsed = $derived(uiStore.sidebarCollapsed);
    const folders = $derived(dashboardStore.folders);
    const dashboards = $derived(dashboardStore.allDashboards);
    const nonEmptyFolders = $derived(folders.filter(f => inFolder(f.id).length > 0));

    function inFolder(folderId: string): DashboardInfo[] {
        return dashboards
            .filter(d => d.folder_id === folderId)
            .sort((a, b) => a.sort_order - b.sort_order);
    }
    const ungrouped = $derived(
        dashboards.filter(d => !d.folder_id).sort((a, b) => a.sort_order - b.sort_order)
    );

    function toggleFolder(id: string) {
        folderCollapsed = { ...folderCollapsed, [id]: !folderCollapsed[id] };
    }

    // ── Inline editing ───────────────────────────────────────────────────────
    function startInline(kind: 'dash' | 'folder', id: string, current: string) {
        cancelCreate();
        inline = { kind, id };
        inlineValue = current;
    }
    function commitInline() {
        if (!inline) return;
        if (inline.kind === 'dash') dashboardStore.renameDashboard(inline.id, inlineValue);
        else dashboardStore.renameFolder(inline.id, inlineValue);
        inline = null;
    }
    function cancelInline() { inline = null; }
    function inlineKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') { e.preventDefault(); commitInline(); }
        else if (e.key === 'Escape') { e.preventDefault(); cancelInline(); }
    }
    function selectOnMount(node: HTMLInputElement) {
        node.focus();
        node.select();
    }
    function rowKeydown(e: KeyboardEvent, d: DashboardInfo) {
        if (e.key === 'F2') { e.preventDefault(); startInline('dash', d.id, d.name); }
    }

    // ── Dialog actions ───────────────────────────────────────────────────────
    function openEdit(d: DashboardInfo) {
        editTarget = d; editName = d.name; editDesc = d.description ?? ''; editOpen = true;
    }
    function submitEdit() {
        if (editTarget) dashboardStore.updateDashboard(editTarget.id, editName, editDesc);
        editOpen = false;
    }
    function openDelete(d: DashboardInfo) { deleteTarget = d; deleteOpen = true; }
    function confirmDelete() {
        if (deleteTarget) dashboardStore.deleteDashboardById(deleteTarget.id);
        deleteOpen = false;
    }
    function openDeleteGroup(id: string, name: string) { deleteGroupTarget = { id, name }; deleteGroupOpen = true; }
    function confirmDeleteGroup() {
        if (deleteGroupTarget) dashboardStore.deleteFolder(deleteGroupTarget.id);
        deleteGroupOpen = false;
    }

    // ── Sidebar position/selection (VSCode-style) ────────────────────────────
    // The user's chosen creation target: a folder id, or null for the root.
    // This is DISTINCT from the active dashboard (dashboardStore.dashboardId):
    // clicking a folder — or the empty root area — sets where the next new
    // dashboard lands, regardless of whether that folder already has contents.
    let selectedFolderId = $state<string | null>(null);
    function selectFolder(id: string) { selectedFolderId = id; }
    function selectRoot() { selectedFolderId = null; }

    // ── Inline creation (VSCode-style) ───────────────────────────────────────
    function newDashboard() {
        // Guard a stale selection (its folder was deleted) → fall back to root.
        const target = selectedFolderId && folders.some(f => f.id === selectedFolderId)
            ? selectedFolderId
            : null;
        startCreate('dash', target);
    }
    // Folders never nest for now → a new group is always created at the root.
    function newGroup() { startCreate('folder', null); }

    function startCreate(kind: 'dash' | 'folder', folderId: string | null) {
        inline = null;
        creating = { kind, folderId };
        creatingValue = '';
        creatingError = '';
        // Reveal the input if the target folder was collapsed.
        if (folderId) folderCollapsed = { ...folderCollapsed, [folderId]: false };
    }
    function cancelCreate() {
        creating = null;
        creatingValue = '';
        creatingError = '';
    }
    function commitCreate() {
        if (!creating) return;
        const name = creatingValue.trim();
        if (!name) {
            creatingError = creating.kind === 'folder'
                ? 'Debes especificar un nombre para la carpeta'
                : 'Debes especificar un nombre para el dashboard';
            return;
        }
        if (creating.kind === 'folder') dashboardStore.createFolder(name);
        else dashboardStore.createDashboard(name, creating.folderId);
        cancelCreate();
    }
    function createKeydown(e: KeyboardEvent) {
        if (e.key === 'Enter') { e.preventDefault(); commitCreate(); }
        else if (e.key === 'Escape') { e.preventDefault(); cancelCreate(); }
    }
    // Blur commits a filled name (VSCode) or quietly cancels an empty one.
    function createBlur() {
        if (!creating) return;
        if (creatingValue.trim()) commitCreate();
        else cancelCreate();
    }

    // ── Drag & drop ──────────────────────────────────────────────────────────
    function container(folderId: string | null): string {
        return `dnd-${folderId ?? 'root'}`;
    }
    // Drop onto a row → reorder relative to it (and move folders if needed).
    function onRowDrop(state: DragDropState<DashboardInfo>, targetDash: DashboardInfo) {
        const drag = state.draggedItem;
        if (!drag || drag.id === targetDash.id) return;
        dashboardStore.reorderDashboard(
            drag.id,
            targetDash.id,
            state.dropPosition ?? 'before',
            targetDash.folder_id ?? null,
        );
    }
    // Drop onto a folder header / root zone → move into it (append).
    function onFolderDrop(state: DragDropState<DashboardInfo>, folderId: string | null) {
        const drag = state.draggedItem;
        if (!drag || (drag.folder_id ?? null) === folderId) return;
        dashboardStore.moveDashboardToFolder(drag.id, folderId);
    }
</script>

<!-- ── Edit-mode row: draggable + droppable, inline edit, management menu ────── -->
{#snippet editRow(d: DashboardInfo, indented: boolean)}
    {@const IconCmp = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
    <div
        class="row"
        class:active={d.id === dashboardStore.dashboardId}
        class:indented
        use:draggable={{ container: container(d.folder_id ?? null), dragData: d, handle: '.drag-handle', disabled: !!inline, attributes: { draggingClass: 'svelte-dnd-dragging' } }}
        use:droppable={{ container: container(d.folder_id ?? null), callbacks: { onDrop: (s) => onRowDrop(s as DragDropState<DashboardInfo>, d) } }}
    >
        {#if inline?.kind === 'dash' && inline.id === d.id}
            <span class="row-icon inline-icon"><IconCmp size={14} /></span>
            <input
                class="inline-input"
                bind:value={inlineValue}
                use:selectOnMount
                onkeydown={inlineKeydown}
                onblur={commitInline}
            />
        {:else}
            <span class="drag-handle" aria-hidden="true" title="Drag to reorder or move"><GripVerticalIcon size={12} /></span>
            <button
                class="row-main"
                onclick={() => { selectedFolderId = d.folder_id ?? null; dashboardStore.loadDashboard(d.id); }}
                ondblclick={() => startInline('dash', d.id, d.name)}
                onkeydown={(e) => rowKeydown(e, d)}
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
                    <DropdownMenu.Item onSelect={() => startInline('dash', d.id, d.name)}>
                        <PencilIcon class="size-4" /> Rename (inline)
                    </DropdownMenu.Item>
                    <DropdownMenu.Item onSelect={() => openEdit(d)}>
                        <PencilIcon class="size-4" /> Edit name & description
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
        {/if}
    </div>
{/snippet}

<!-- ── Preview-mode row: navigation only ───────────────────────────────────── -->
{#snippet previewRow(d: DashboardInfo)}
    {@const IconCmp = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
    <button
        class="row-main preview-row"
        class:active={d.id === dashboardStore.dashboardId}
        onclick={() => dashboardStore.loadDashboard(d.id)}
        title={d.description || d.name}
    >
        <span class="row-icon"><IconCmp size={14} /></span>
        <span class="row-name">{d.name}</span>
    </button>
{/snippet}

<!-- ── Collapsed rail icon ─────────────────────────────────────────────────── -->
{#snippet railIcon(d: DashboardInfo)}
    {@const IconCmp = resolveDashboardIcon(d.dashboard_hint, d.dashboard_domain)}
    <Tooltip.Root>
        <Tooltip.Trigger
            class="rail-icon {d.id === dashboardStore.dashboardId ? 'active' : ''}"
            onclick={() => dashboardStore.loadDashboard(d.id)}
            aria-label={d.name}
        >
            <IconCmp size={16} />
        </Tooltip.Trigger>
        <Tooltip.Content side="right">{d.name}</Tooltip.Content>
    </Tooltip.Root>
{/snippet}

<!-- ── Inline creation input (folder or dashboard) ─────────────────────────── -->
{#snippet createRow(indented: boolean)}
    {@const IconCmp = creating?.kind === 'folder' ? FolderIcon : resolveDashboardIcon(null, null)}
    <div class="create-wrap" class:indented>
        <div class="create-input-row">
            <span class="row-icon inline-icon"><IconCmp size={14} /></span>
            <input
                class="inline-input"
                bind:value={creatingValue}
                use:selectOnMount
                onkeydown={createKeydown}
                onblur={createBlur}
                placeholder={creating?.kind === 'folder' ? 'Nombre de la carpeta' : 'Nombre del dashboard'}
                aria-label={creating?.kind === 'folder' ? 'New group name' : 'New dashboard name'}
            />
        </div>
        {#if creatingError}
            <p class="create-error">{creatingError}</p>
        {/if}
    </div>
{/snippet}

<nav class="explorer" class:collapsed aria-label={$editMode ? 'Dashboard explorer' : 'Dashboard navigation'}>
    <div class="explorer-header" class:collapsed>
        {#if !collapsed}
            <span class="explorer-title">{$editMode ? 'Explorer' : 'Dashboards'}</span>
            <div class="explorer-actions">
                {#if $editMode}
                    <button class="hbtn" onclick={newGroup} title="New group" aria-label="New group">
                        <FolderPlusIcon size={15} />
                    </button>
                    <button class="hbtn" onclick={newDashboard} title="New dashboard" aria-label="New dashboard">
                        <PlusIcon size={16} />
                    </button>
                {/if}
                <button class="hbtn" onclick={uiStore.toggleSidebar} title="Collapse sidebar" aria-label="Collapse sidebar">
                    <PanelLeftCloseIcon size={16} />
                </button>
            </div>
        {:else}
            <button class="hbtn" onclick={uiStore.toggleSidebar} title="Expand sidebar" aria-label="Expand sidebar">
                <PanelLeftOpenIcon size={16} />
            </button>
        {/if}
    </div>

    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="explorer-body"
        onclick={(e) => { if ($editMode && e.target === e.currentTarget) selectRoot(); }}
    >
        {#if dashboardStore.dashboardsLoading}
            {#each Array(5) as _, i (i)}
                {#if collapsed}
                    <div class="skeleton-rail"><Skeleton class="size-7 rounded-md" /></div>
                {:else}
                    <div class="skeleton-row">
                        <Skeleton class="size-4 rounded" />
                        <Skeleton class="h-3.5 flex-1 rounded" />
                    </div>
                {/if}
            {/each}

        {:else if collapsed}
            <Tooltip.Provider delayDuration={200}>
                {#each nonEmptyFolders as f (f.id)}
                    {#each inFolder(f.id) as d (d.id)}
                        {@render railIcon(d)}
                    {/each}
                    <div class="rail-sep"></div>
                {/each}
                {#each ungrouped as d (d.id)}
                    {@render railIcon(d)}
                {/each}
            </Tooltip.Provider>

        {:else if $editMode}
            <!-- New folder input (always at root — folders don't nest) -->
            {#if creating?.kind === 'folder'}
                {@render createRow(false)}
            {/if}
            {#each folders as f (f.id)}
                <div
                    class="folder-header-wrap"
                    class:selected={selectedFolderId === f.id}
                    use:droppable={{ container: container(f.id), callbacks: { onDrop: (s) => onFolderDrop(s as DragDropState<DashboardInfo>, f.id) } }}
                >
                    {#if inline?.kind === 'folder' && inline.id === f.id}
                        <span class="chev open"><ChevronRightIcon size={14} /></span>
                        <FolderIcon size={14} />
                        <input class="inline-input folder-inline" bind:value={inlineValue}
                            use:selectOnMount onkeydown={inlineKeydown} onblur={commitInline} />
                    {:else}
                        <button
                            class="folder-header"
                            onclick={() => { selectFolder(f.id); toggleFolder(f.id); }}
                            ondblclick={() => startInline('folder', f.id, f.name)}
                            onkeydown={(e) => { if (e.key === 'F2') { e.preventDefault(); startInline('folder', f.id, f.name); } }}
                        >
                            <span class="chev" class:open={!folderCollapsed[f.id]}><ChevronRightIcon size={14} /></span>
                            <FolderIcon size={14} />
                            <span class="folder-name">{f.name}</span>
                            <span class="folder-count">{inFolder(f.id).length}</span>
                        </button>
                        <DropdownMenu.Root
                            open={openFolderMenuId === f.id}
                            onOpenChange={(o) => { openFolderMenuId = o ? f.id : (openFolderMenuId === f.id ? null : openFolderMenuId); }}
                        >
                            <DropdownMenu.Trigger class="row-kebab folder-kebab" aria-label="Group options">
                                <EllipsisIcon size={14} />
                            </DropdownMenu.Trigger>
                            <DropdownMenu.Content align="start" class="w-44">
                                <DropdownMenu.Item onSelect={() => startInline('folder', f.id, f.name)}>
                                    <PencilIcon class="size-4" /> Rename group
                                </DropdownMenu.Item>
                                <DropdownMenu.Separator />
                                <DropdownMenu.Item variant="destructive" onSelect={() => openDeleteGroup(f.id, f.name)}>
                                    <Trash2Icon class="size-4" /> Delete group
                                </DropdownMenu.Item>
                            </DropdownMenu.Content>
                        </DropdownMenu.Root>
                    {/if}
                </div>
                {#if !folderCollapsed[f.id]}
                    {#if creating?.kind === 'dash' && creating.folderId === f.id}
                        {@render createRow(true)}
                    {/if}
                    {#each inFolder(f.id) as d (d.id)}
                        {@render editRow(d, true)}
                    {/each}
                {/if}
            {/each}

            <!-- Root drop zone (also holds ungrouped dashboards). Clicking its
                 empty area selects the root as the creation target. -->
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
                class="root-dropzone"
                class:selected={selectedFolderId === null}
                onclick={(e) => { if (e.target === e.currentTarget) selectRoot(); }}
                use:droppable={{ container: container(null), callbacks: { onDrop: (s) => onFolderDrop(s as DragDropState<DashboardInfo>, null) } }}
            >
                {#if creating?.kind === 'dash' && creating.folderId === null}
                    {@render createRow(false)}
                {/if}
                {#each ungrouped as d (d.id)}
                    {@render editRow(d, false)}
                {/each}
                {#if dashboards.length === 0 && !creating}
                    <p class="empty">No dashboards yet. Create one with the + button.</p>
                {/if}
            </div>

        {:else}
            {#each nonEmptyFolders as f (f.id)}
                <div class="group-label"><span>{f.name}</span><span class="group-line"></span></div>
                {#each inFolder(f.id) as d (d.id)}
                    {@render previewRow(d)}
                {/each}
            {/each}
            {#if ungrouped.length > 0 && nonEmptyFolders.length > 0}
                <div class="group-gap"></div>
            {/if}
            {#each ungrouped as d (d.id)}
                {@render previewRow(d)}
            {/each}
            {#if dashboards.length === 0}
                <p class="empty">No dashboards yet.</p>
            {/if}
        {/if}
    </div>

    {#if !collapsed && $editMode}
        <div class="explorer-footer">
            <Button variant="secondary" size="sm" class="w-full justify-start gap-2" onclick={newDashboard}>
                <PlusIcon class="size-4" /> New Dashboard
            </Button>
        </div>
    {/if}
</nav>

<!-- Edit name + description (single step) -->
<Dialog.Root bind:open={editOpen}>
    <Dialog.Content class="sm:max-w-md">
        <Dialog.Header><Dialog.Title>Edit dashboard</Dialog.Title></Dialog.Header>
        <div class="dialog-fields">
            <label class="field-label" for="edit-name">Name</label>
            <Input id="edit-name" bind:value={editName} placeholder="Dashboard name"
                onkeydown={(e) => e.key === 'Enter' && submitEdit()} />
            <label class="field-label" for="edit-desc">Description</label>
            <Input id="edit-desc" bind:value={editDesc} placeholder="Short description (optional)"
                onkeydown={(e) => e.key === 'Enter' && submitEdit()} />
        </div>
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (editOpen = false)}>Cancel</Button>
            <Button size="sm" onclick={submitEdit}>Save</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<!-- Delete dashboard -->
<Dialog.Root bind:open={deleteOpen}>
    <Dialog.Content class="sm:max-w-sm">
        <Dialog.Header>
            <Dialog.Title>Delete dashboard</Dialog.Title>
            <Dialog.Description>
                "{deleteTarget?.name}" and its panels will be permanently deleted. This cannot be undone.
            </Dialog.Description>
        </Dialog.Header>
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (deleteOpen = false)}>Cancel</Button>
            <Button variant="destructive" size="sm" onclick={confirmDelete}>Delete</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>

<!-- Delete group -->
<Dialog.Root bind:open={deleteGroupOpen}>
    <Dialog.Content class="sm:max-w-sm">
        <Dialog.Header>
            <Dialog.Title>Delete group</Dialog.Title>
            <Dialog.Description>
                "{deleteGroupTarget?.name}" will be removed. Its dashboards are kept and moved to the root.
            </Dialog.Description>
        </Dialog.Header>
        <Dialog.Footer>
            <Button variant="ghost" size="sm" onclick={() => (deleteGroupOpen = false)}>Cancel</Button>
            <Button variant="destructive" size="sm" onclick={confirmDeleteGroup}>Delete group</Button>
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
        transition: width 0.2s ease;
    }
    .explorer.collapsed { width: 52px; }

    .explorer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.25rem;
        padding: 0.5rem 0.5rem 0.5rem 0.875rem;
        flex-shrink: 0;
        min-height: 40px;
    }
    .explorer-header.collapsed { justify-content: center; padding: 0.5rem 0; }

    .explorer-title {
        font-size: 0.6875rem;
        font-weight: 600;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: var(--sqlviz-text-muted);
        white-space: nowrap;
        overflow: hidden;
    }

    .explorer-actions { display: flex; gap: 0.125rem; flex-shrink: 0; }

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
        display: flex;
        flex-direction: column;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 0 0.375rem 0.5rem;
    }
    /* Keep tree items at their natural height so the body scrolls instead of
       squishing them — only the root zone is allowed to grow. */
    .explorer-body > * { flex-shrink: 0; }
    .explorer.collapsed .explorer-body {
        padding: 0.25rem 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.125rem;
    }

    .skeleton-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.4375rem 0.5rem; }
    .skeleton-rail { padding: 0.25rem 0; }

    :global(.rail-icon) {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border: none;
        background: none;
        color: var(--sqlviz-text-muted);
        border-radius: var(--sqlviz-radius);
        cursor: pointer;
        transition: background 0.12s, color 0.12s;
    }
    :global(.rail-icon:hover) { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    :global(.rail-icon.active) {
        background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent);
        color: var(--sqlviz-primary);
    }
    .rail-sep { width: 24px; height: 1px; margin: 0.25rem 0; background: var(--sqlviz-hairline); }

    .folder-header-wrap {
        position: relative;
        display: flex;
        align-items: center;
        margin-top: 0.125rem;
        border-radius: var(--sqlviz-radius);
    }
    /* VSCode-style selection: a thin primary line on the left edge only — no
       box, no fill. The filled highlight stays reserved for the active
       dashboard (.row.active), keeping position and active clearly distinct. */
    .folder-header-wrap.selected::before,
    .root-dropzone.selected::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 2px;
        background: var(--sqlviz-primary);
    }
    .folder-header {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        flex: 1;
        min-width: 0;
        padding: 0.375rem 0.5rem;
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

    /* Ungrouped dashboards sit here as loose items directly in the sidebar; the
       zone itself is invisible — it only provides the empty click target and,
       when the root is the selected creation target, the thin left line. */
    .root-dropzone {
        position: relative;
        /* Fill all remaining vertical space so the root is one continuous zone
           down to the bottom — and its left selection line spans the whole
           area, VSCode-style. Never shrinks below its content. */
        flex: 1 0 auto;
        min-height: 96px;
    }

    .group-label { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 0.5rem 0.375rem; }
    .group-label span:first-child {
        font-size: 0.6875rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--sqlviz-text-muted);
        white-space: nowrap;
    }
    .group-line { flex: 1; height: 1px; background: var(--sqlviz-hairline); }
    .group-gap { height: 0.75rem; }

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

    .preview-row {
        width: 100%;
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text-muted);
        transition: background 0.12s, color 0.12s;
    }
    .preview-row:hover { background: var(--sqlviz-bg-base); color: var(--sqlviz-text); }
    .preview-row.active { background: color-mix(in srgb, var(--sqlviz-primary) 15%, transparent); color: var(--sqlviz-primary); }

    .drag-handle {
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        width: 14px;
        margin-left: 0.125rem;
        color: var(--sqlviz-text-muted);
        cursor: grab;
        opacity: 0;
        transition: opacity 0.12s;
    }
    .row:hover .drag-handle { opacity: 0.6; }
    .drag-handle:hover { opacity: 1 !important; }
    .drag-handle:active { cursor: grabbing; }

    .row-icon { flex-shrink: 0; display: flex; align-items: center; }
    .inline-icon { padding-left: 0.5rem; }
    .row-name {
        font-size: 0.8125rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 1.3;
    }

    .inline-input {
        flex: 1;
        min-width: 0;
        margin: 0.25rem 0.375rem 0.25rem 0.5rem;
        padding: 0.125rem 0.375rem;
        font-size: 0.8125rem;
        background: var(--sqlviz-bg);
        color: var(--sqlviz-text);
        border: 1px solid var(--sqlviz-primary);
        border-radius: var(--sqlviz-radius);
        outline: none;
    }
    .folder-inline { font-weight: 600; }

    /* Inline creation (VSCode-style) */
    .create-wrap { display: flex; flex-direction: column; }
    .create-wrap.indented { margin-left: 0.75rem; }
    .create-input-row { display: flex; align-items: center; }
    .create-error {
        margin: 0 0 0.375rem 1.375rem;
        font-size: 0.6875rem;
        line-height: 1.3;
        color: var(--sqlviz-negative);
        opacity: 0.85;
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
    .row.active :global(.row-kebab),
    .folder-header-wrap:hover :global(.folder-kebab) { opacity: 1; }
    :global(.row-kebab:hover) { background: var(--sqlviz-border); color: var(--sqlviz-text); }

    .empty { padding: 0.75rem 0.5rem; font-size: 0.75rem; color: var(--sqlviz-text-muted); line-height: 1.4; }

    .explorer-footer { padding: 0.5rem; border-top: 1px solid var(--sqlviz-hairline); flex-shrink: 0; }

    .dialog-fields { display: flex; flex-direction: column; gap: 0.375rem; }
    .field-label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        margin-top: 0.25rem;
    }
</style>
