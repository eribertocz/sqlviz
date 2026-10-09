import type { SqlStatement } from './sqlScript.svelte';
import type { SqlRunResolution } from './sqlRunResolution';
import { runResolutionComplete } from './sqlRunResolution';

export type SqlScriptSnapshot = {
    version: 1;
    dashboard_id: string;
    revision: string;
    draft_source: string;
    panels: { id: string; name: string; sql_content: string; sort_order: number }[];
    publication: null | {
        version: 1; revision: number; source: string;
        bindings: { statement_index: number; panel_id: string; start_offset: number; end_offset: number }[];
    };
};
export type SqlScriptCommit = {
    version: 1;
    snapshot: SqlScriptSnapshot;
    created_panels: { creation_key: string; panel_id: string }[];
};

/** A fresh token may not silently adopt a changed panel set or changed SQL. */
export function requireSqlRunSnapshot(snapshot: SqlScriptSnapshot, dashboardId: string,
    panels: readonly { id: string; sql: string }[]): void {
    if (snapshot?.version !== 1 || snapshot.dashboard_id !== dashboardId ||
        !/^sql-script-v1:[0-9a-f]{64}$/.test(snapshot.revision) || !Array.isArray(snapshot.panels) ||
        snapshot.panels.length !== panels.length || new Set(snapshot.panels.map(panel => panel.id)).size !== panels.length ||
        panels.some(panel => !snapshot.panels.some(saved => saved.id === panel.id && saved.sql_content === panel.sql))) {
        throw new Error('Dashboard definitions changed. Reload the dashboard and review query associations.');
    }
}

/** Adopt IDs only from a verified commit receipt, never from order or SQL matching. */
export function requireSqlRunCommit(receipt: SqlScriptCommit, dashboardId: string,
    resolution: SqlRunResolution): { ids: string[]; statements: SqlStatement[] } {
    const fail = () => { throw new Error('Could not verify saved definitions. Reload the dashboard before running again.'); };
    const saved = receipt?.snapshot;
    const publication = saved?.publication;
    if (!runResolutionComplete(resolution) || receipt?.version !== 1 || saved?.version !== 1 ||
        saved.dashboard_id !== dashboardId || !/^sql-script-v1:[0-9a-f]{64}$/.test(saved.revision) ||
        saved.revision === resolution.expectedRevision || saved.draft_source !== resolution.source ||
        publication?.version !== 1 || !Number.isSafeInteger(publication.revision) || publication.revision < 1 ||
        publication.source !== resolution.source || !Array.isArray(saved.panels) ||
        !Array.isArray(publication.bindings) || !Array.isArray(receipt.created_panels) ||
        publication.bindings.length !== resolution.statements.length || saved.panels.length !== resolution.statements.length) return fail();
    const created = new Map(receipt.created_panels.map(item => [item.creation_key, item.panel_id]));
    const choices = resolution.choices.filter(item => item.kind !== 'remove');
    if (created.size !== receipt.created_panels.length ||
        created.size !== choices.filter(item => item.kind === 'create').length) return fail();
    const ids: string[] = [];
    const statements: SqlStatement[] = [];
    for (const [index, binding] of publication.bindings.entries()) {
        const statement = resolution.statements[index];
        const choice = choices.find(item => item.statement_index === index);
        const id = choice?.kind === 'keep' ? choice.panel_id : choice?.kind === 'create' ? created.get(choice.creation_key) : null;
        const panel = saved.panels.find(item => item.id === id);
        if (!id || binding.statement_index !== index || binding.panel_id !== id ||
            binding.start_offset !== statement.start_offset || binding.end_offset !== statement.end_offset ||
            !panel || panel.sql_content !== statement.sql || panel.sort_order !== index || ids.includes(id) ||
            (choice?.kind === 'create' && resolution.panels.some(previous => previous.id === id))) return fail();
        ids.push(id);
        statements.push({ ...statement });
    }
    if (new Set(saved.panels.map(panel => panel.id)).size !== ids.length) return fail();
    return { ids, statements };
}
