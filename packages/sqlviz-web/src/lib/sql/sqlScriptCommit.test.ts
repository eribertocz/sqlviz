import { expect, it } from 'vitest';
import { requireSqlRunCommit, requireSqlRunSnapshot, type SqlScriptCommit } from './sqlScriptCommit';
import type { SqlRunResolution } from './sqlRunResolution';

function fixture(): { resolution: SqlRunResolution; receipt: SqlScriptCommit } {
    const resolution: SqlRunResolution = {
        source: 'SELECT 2; SELECT 3', expectedRevision: `sql-script-v1:${'0'.repeat(64)}`,
        statements: [{ sql: 'SELECT 2', start_offset: 0, end_offset: 8 },
            { sql: 'SELECT 3', start_offset: 10, end_offset: 18 }],
        panels: [{ id: 'a', label: 'A', sql: 'SELECT 1' }, { id: 'b', label: 'B', sql: 'SELECT 4' }],
        choices: [{ kind: 'keep', statement_index: 0, panel_id: 'a' },
            { kind: 'create', statement_index: 1, creation_key: 'new' }, { kind: 'remove', panel_id: 'b' }],
    };
    const receipt: SqlScriptCommit = { version: 1, created_panels: [{ creation_key: 'new', panel_id: 'c' }],
        snapshot: { version: 1, dashboard_id: 'd', revision: `sql-script-v1:${'1'.repeat(64)}`,
            definition_revision: `sql-definition-v1:${'1'.repeat(64)}`, draft_source: resolution.source,
            panels: [{ id: 'a', name: 'A', sql_content: 'SELECT 2', sort_order: 0 },
                { id: 'c', name: 'New', sql_content: 'SELECT 3', sort_order: 1 }],
            publication: { version: 1, revision: 1, source: resolution.source, bindings: [
                { statement_index: 0, panel_id: 'a', start_offset: 0, end_offset: 8 },
                { statement_index: 1, panel_id: 'c', start_offset: 10, end_offset: 18 },
            ] },
        } };
    return { resolution, receipt };
}

it('adopts only explicit existing IDs and correlated creations from the committed source', () => {
    const { resolution, receipt } = fixture();
    expect(requireSqlRunCommit(receipt, 'd', resolution)).toEqual({ ids: ['a', 'c'], statements: resolution.statements,
        definition: { version: 1, dashboard_id: 'd', revision: receipt.snapshot.definition_revision } });
    expect(receipt.created_panels[0].creation_key).toBe('new');
});

it.each(['dashboard', 'token', 'definition', 'same-token', 'source', 'binding', 'offset', 'sql', 'order', 'duplicate', 'missing', 'creation', 'old-id', 'counter'])
('does not execute after an inconsistent %s receipt', field => {
    const { resolution, receipt } = fixture();
    const saved = receipt.snapshot;
    if (field === 'dashboard') saved.dashboard_id = 'foreign';
    if (field === 'token') saved.revision = 'opaque-invalid-token';
    if (field === 'definition') saved.definition_revision = null;
    if (field === 'same-token') saved.revision = resolution.expectedRevision!;
    if (field === 'source') saved.publication!.source = 'SELECT 99';
    if (field === 'binding') saved.publication!.bindings[0].panel_id = 'b';
    if (field === 'offset') saved.publication!.bindings[0].start_offset = 1;
    if (field === 'sql') saved.panels[0].sql_content = 'SELECT 99';
    if (field === 'order') saved.panels[0].sort_order = 1;
    if (field === 'duplicate') saved.panels[1] = saved.panels[0];
    if (field === 'missing') saved.publication = null;
    if (field === 'creation') receipt.created_panels[0].creation_key = 'different';
    if (field === 'old-id') receipt.created_panels[0].panel_id = 'b';
    if (field === 'counter') saved.publication!.revision = 0;
    expect(() => requireSqlRunCommit(receipt, 'd', resolution)).toThrow('Reload');
});

it('requires unchanged persisted SQL and the exact ID set before a fresh Run snapshot', () => {
    const snapshot = fixture().receipt.snapshot;
    const panels = snapshot.panels.map(panel => ({ id: panel.id, sql: panel.sql_content })).reverse();
    expect(() => requireSqlRunSnapshot(snapshot, 'd', panels)).not.toThrow();
    expect(() => requireSqlRunSnapshot(snapshot, 'foreign', panels)).toThrow('Reload');
    expect(() => requireSqlRunSnapshot(snapshot, 'd', panels.slice(1))).toThrow('Reload');
    expect(() => requireSqlRunSnapshot(snapshot, 'd', panels.map(panel => ({ ...panel, sql: 'SELECT 99' })))).toThrow('Reload');
});
