import type { SqlStatement } from './sqlScript.svelte';

export type SqlTextEdit = Readonly<{ rangeOffset: number; rangeLength: number; text: string }>;
export type SqlEditorChange = Readonly<{
    before: string;
    after: string;
    changes: readonly SqlTextEdit[];
    isFlush: boolean;
}>;
type Binding = Readonly<{ panel_id: string; start_offset: number; end_offset: number }>;
export type SqlIdentityDraft = Readonly<{
    source: string;
    panel_ids: readonly string[];
    bindings: readonly Binding[];
}>;
export type SqlIdentityProjection = Readonly<{
    source: string;
    statements: readonly Readonly<{ statement_index: number; panel_id: string | null }>[];
    unresolved_panel_ids: readonly string[];
}>;

function snapshot(source: string, panelIds: readonly string[], bindings: readonly Binding[]): SqlIdentityDraft {
    if (panelIds.length > 256 || new Set(panelIds).size !== panelIds.length ||
        panelIds.some(id => typeof id !== 'string' || !id.trim())) {
        throw new Error('Invalid SQL panel snapshot');
    }
    return Object.freeze({ source, panel_ids: Object.freeze([...panelIds]),
        bindings: Object.freeze(bindings.map(binding => Object.freeze({ ...binding }))) });
}

/** A source replacement has no identity evidence, even when its SQL looks familiar. */
export function unboundSqlDraft(source: string, panelIds: readonly string[] = []): SqlIdentityDraft {
    return snapshot(source, panelIds, []);
}

function validateStatements(source: string, statements: readonly SqlStatement[]) {
    let end = 0;
    if (statements.length > 256) throw new Error('Too many SQL statements');
    for (const statement of statements) {
        if (!Number.isInteger(statement.start_offset) || !Number.isInteger(statement.end_offset) ||
            statement.start_offset < end || statement.end_offset <= statement.start_offset ||
            statement.end_offset > source.length || !statement.sql.trim() ||
            source.slice(statement.start_offset, statement.end_offset) !== statement.sql) {
            throw new Error('SQL source positions do not match this draft');
        }
        end = statement.end_offset;
    }
}

/** The caller supplies known execution correspondence, never a SQL matching heuristic. */
export function confirmedSqlDraft(source: string,
    assignments: readonly Readonly<{ panel_id: string; statement: SqlStatement }>[]): SqlIdentityDraft {
    validateStatements(source, assignments.map(item => item.statement));
    return snapshot(source, assignments.map(item => item.panel_id), assignments.map(item => ({
        panel_id: item.panel_id, start_offset: item.statement.start_offset, end_offset: item.statement.end_offset,
    })));
}

/** Only for text constructed directly from paired persisted panels, not saved arbitrary drafts. */
export function sqlDraftFromPanels(panels: readonly Readonly<{ id: string; sql_content: string }>[]): SqlIdentityDraft {
    let source = '';
    const bindings: Binding[] = [];
    for (const [index, panel] of panels.entries()) {
        if (index > 0) source += '\n;\n\n';
        const start_offset = source.length;
        source += panel.sql_content;
        if (panel.sql_content.trim()) bindings.push({ panel_id: panel.id, start_offset, end_offset: source.length });
    }
    return snapshot(source, panels.map(panel => panel.id), bindings);
}

/** Apply Monaco's simultaneous UTF-16 edits to tracked ranges, without parsing SQL. */
export function editSqlIdentityDraft(draft: SqlIdentityDraft, event: SqlEditorChange): SqlIdentityDraft {
    const unbound = () => unboundSqlDraft(event.after, draft.panel_ids);
    if (event.before !== draft.source || event.isFlush || event.changes.length > 1024) return unbound();
    const edits = [...event.changes].sort((a, b) => a.rangeOffset - b.rangeOffset);
    let cursor = 0;
    let rebuilt = '';
    for (let i = 0; i < edits.length; i++) {
        const edit = edits[i];
        if (!Number.isInteger(edit.rangeOffset) || !Number.isInteger(edit.rangeLength) ||
            edit.rangeOffset < cursor || edit.rangeLength < 0 ||
            edit.rangeOffset + edit.rangeLength > draft.source.length || typeof edit.text !== 'string' ||
            (i > 0 && edit.rangeOffset === edits[i - 1].rangeOffset)) return unbound();
        rebuilt += draft.source.slice(cursor, edit.rangeOffset) + edit.text;
        cursor = edit.rangeOffset + edit.rangeLength;
    }
    if (rebuilt + draft.source.slice(cursor) !== event.after) return unbound();

    const bindings: Binding[] = [];
    for (const binding of draft.bindings) {
        let shift = 0;
        let growth = 0;
        let keep = true;
        for (const edit of edits) {
            const start = edit.rangeOffset;
            const end = start + edit.rangeLength;
            const delta = edit.text.length - edit.rangeLength;
            // Insertions exactly on a boundary are outside the owned block.
            if (end <= binding.start_offset) shift += delta;
            else if (start >= binding.end_offset) continue;
            else if (start >= binding.start_offset && end <= binding.end_offset &&
                !(start === binding.start_offset && end === binding.end_offset)) growth += delta;
            else { keep = false; break; }
        }
        const start_offset = binding.start_offset + shift;
        const end_offset = binding.end_offset + shift + growth;
        if (keep && end_offset > start_offset) bindings.push({ ...binding, start_offset, end_offset });
    }
    return snapshot(event.after, draft.panel_ids, bindings);
}

/** Native parsing must still confirm one complete statement per tracked block. */
export function projectSqlIdentity(draft: SqlIdentityDraft, statements: readonly SqlStatement[]): SqlIdentityProjection {
    validateStatements(draft.source, statements);
    const matched = new Set<string>();
    const candidates = new Map<number, string[]>();
    for (const binding of draft.bindings) {
        const overlaps = statements.map((statement, index) => ({ statement, index })).filter(
            ({ statement }) => statement.start_offset < binding.end_offset && statement.end_offset > binding.start_offset,
        );
        if (overlaps.length !== 1) continue;
        const { statement, index } = overlaps[0];
        if (statement.start_offset < binding.start_offset || statement.end_offset > binding.end_offset) continue;
        candidates.set(index, [...(candidates.get(index) ?? []), binding.panel_id]);
    }
    const resolved = statements.map((_statement, statement_index) => {
        const owners = candidates.get(statement_index) ?? [];
        const panel_id = owners.length === 1 ? owners[0] : null;
        if (panel_id) matched.add(panel_id);
        return Object.freeze({ statement_index, panel_id });
    });
    return Object.freeze({ source: draft.source, statements: Object.freeze(resolved),
        unresolved_panel_ids: Object.freeze(draft.panel_ids.filter(id => !matched.has(id))) });
}

/** Once a successful parse loses correspondence, later text equality cannot resurrect it. */
export function settleSqlIdentityDraft(draft: SqlIdentityDraft, statements: readonly SqlStatement[]): SqlIdentityDraft {
    const projection = projectSqlIdentity(draft, statements);
    const matched = new Set(projection.statements.map(item => item.panel_id));
    const bindings = draft.bindings.filter(binding => matched.has(binding.panel_id));
    return bindings.length === draft.bindings.length ? draft : snapshot(draft.source, draft.panel_ids, bindings);
}
