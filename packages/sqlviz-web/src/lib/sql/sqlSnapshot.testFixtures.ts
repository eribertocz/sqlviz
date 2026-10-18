import type { SqlScriptSnapshot } from './sqlScriptCommit';

/** Legacy metadata fixture; no invented publication or stored correspondence. */
export function legacySqlSnapshot(id: string, panels: { id: string; sql_content: string; sort_order?: number }[] = [],
    source = ''): SqlScriptSnapshot {
    return { version: 1, dashboard_id: id, revision: `sql-script-v1:${'1'.repeat(64)}`,
        draft_source: source, definition_revision: null, publication: null, publication_status: 'absent',
        last_run_at: null, last_run_sql: null,
        panels: panels.map((panel, index) => ({ ...panel, name: panel.id, sort_order: panel.sort_order ?? index })) };
}
