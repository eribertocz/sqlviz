import { confirmedSqlDraft, sqlDraftFromPanels, unboundSqlDraft, type SqlIdentityDraft } from './sqlIdentityDraft';
import { parseSqlScript, type SqlStatement } from './sqlScript.svelte';
import type { SqlScriptSnapshot } from './sqlScriptCommit';
import type { CachedDashboard } from '$lib/stores/dashboardCache.svelte';

export type LoadedSqlSnapshot = {
    source: string;
    identity: SqlIdentityDraft;
    lastRunIdentity: SqlIdentityDraft | null;
    panels: SqlScriptSnapshot['panels'];
    definitionRevision: string | null;
    lastRunAt: string | null;
    lastRunSql: string;
};

/** Snapshot is the authority; native parsing verifies explicit persisted ranges. */
export async function loadSqlSnapshot(value: unknown, dashboardId: string,
    parse: (source: string) => Promise<SqlStatement[]> = parseSqlScript): Promise<LoadedSqlSnapshot> {
    const fail = (): never => { throw new Error('Could not verify the dashboard snapshot. Reload and review query associations.'); };
    if (!value || typeof value !== 'object') return fail();
    const snapshot = value as SqlScriptSnapshot;
    if (snapshot.version !== 1 || snapshot.dashboard_id !== dashboardId ||
        typeof snapshot.revision !== 'string' || !/^sql-script-v1:[0-9a-f]{64}$/.test(snapshot.revision) ||
        typeof snapshot.draft_source !== 'string' || !Array.isArray(snapshot.panels) || snapshot.panels.length > 256 ||
        !['absent', 'confirmed', 'incompatible'].includes(snapshot.publication_status) ||
        !(snapshot.last_run_sql === null || typeof snapshot.last_run_sql === 'string') ||
        !(snapshot.last_run_at === null || (typeof snapshot.last_run_at === 'string' &&
            /(Z|[+-]\d{2}:\d{2})$/.test(snapshot.last_run_at) && Number.isFinite(Date.parse(snapshot.last_run_at))))) return fail();
    const panels = [...snapshot.panels];
    if (panels.some(panel => !panel || typeof panel.id !== 'string' || !panel.id.trim() || [...panel.id].length > 256 ||
        typeof panel.name !== 'string' || typeof panel.sql_content !== 'string' || !Number.isSafeInteger(panel.sort_order)) ||
        new Set(panels.map(panel => panel.id)).size !== panels.length) return fail();
    panels.sort((a, b) => a.sort_order - b.sort_order);
    const ids = panels.map(panel => panel.id);
    const publication = snapshot.publication;
    let publishedIdentity: SqlIdentityDraft | null = null;
    if (snapshot.publication_status === 'confirmed') {
        if (!publication || publication.version !== 1 || !Number.isSafeInteger(publication.revision) || publication.revision < 1 ||
            typeof publication.source !== 'string' || !Array.isArray(publication.bindings) ||
            publication.bindings.length !== ids.length || typeof snapshot.definition_revision !== 'string' ||
            !/^sql-definition-v1:[0-9a-f]{64}$/.test(snapshot.definition_revision)) return fail();
        const statements = await parse(publication.source);
        if (!Array.isArray(statements) || statements.length !== publication.bindings.length) return fail();
        const assigned = new Set<string>();
        const assignments = publication.bindings.map((binding, index) => {
            const statement = statements[index];
            const panel = panels.find(panel => panel.id === binding?.panel_id);
            if (!binding || binding.statement_index !== index || !panel || assigned.has(panel.id) ||
                !statement || statement.start_offset !== binding.start_offset || statement.end_offset !== binding.end_offset ||
                statement.sql !== panel.sql_content) return fail();
            assigned.add(panel.id);
            return { panel_id: panel.id, statement };
        });
        // Also verifies ranges/slices using UTF-16; never match a query by SQL.
        publishedIdentity = confirmedSqlDraft(publication.source, assignments);
    } else if (publication !== null || snapshot.definition_revision !== null) return fail();
    const legacy = snapshot.publication_status === 'absent' && snapshot.draft_source === '' &&
        snapshot.last_run_at === null && snapshot.last_run_sql === null;
    const legacyIdentity = legacy ? sqlDraftFromPanels(panels) : null;
    const source = legacyIdentity?.source ?? snapshot.draft_source;
    return {
        source, panels, definitionRevision: snapshot.definition_revision,
        identity: publishedIdentity?.source === source ? publishedIdentity : legacyIdentity ?? unboundSqlDraft(source, ids),
        lastRunIdentity: publishedIdentity?.source === snapshot.last_run_sql ? publishedIdentity : null,
        lastRunAt: snapshot.last_run_at, lastRunSql: snapshot.last_run_sql ?? '',
    };
}

/** Cached rows cannot supply definitions or revive a superseded publication. */
export function sqlSnapshotMatchesCache(loaded: LoadedSqlSnapshot, cached: CachedDashboard): boolean {
    if (cached.sql !== loaded.source || (cached.definitionRevision ?? null) !== loaded.definitionRevision ||
        cached.panelIds.length !== loaded.panels.length || cached.panelSQLs.length !== loaded.panels.length ||
        new Set(cached.panelIds).size !== loaded.panels.length) return false;
    const coversPanels = (ids: string[]) => ids.length === loaded.panels.length &&
        new Set(ids).size === ids.length && loaded.panels.every(panel => ids.includes(panel.id));
    if (!coversPanels(cached.executedResults.map(result => result.panel_id)) ||
        (cached.layout !== null && !coversPanels(cached.layout.rows.flatMap(row => row.panels.map(panel => panel.panel_id))))) return false;
    return loaded.panels.every(panel => {
        const index = cached.panelIds.indexOf(panel.id);
        return index >= 0 && cached.panelSQLs[index] === panel.sql_content;
    });
}
