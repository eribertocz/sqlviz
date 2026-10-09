import { expect, it } from 'vitest';
import { initialRunChoices, requireRunPreflight, runResolutionComplete, selectRunPanel, selectRunRemoval,
    type SqlRunPreflight, type SqlRunResolution } from './sqlRunResolution';

function resolution(): SqlRunResolution {
    return { source: 'SELECT 2; SELECT 1', statements: [
        { sql: 'SELECT 2', start_offset: 0, end_offset: 8 }, { sql: 'SELECT 1', start_offset: 10, end_offset: 18 },
    ], panels: [{ id: 'a', label: 'A', sql: 'SELECT 1' }, { id: 'b', label: 'B', sql: 'SELECT 2' }], choices: [] };
}
function complete() {
    const first = selectRunPanel(resolution(), 0, 'b', () => 'new');
    return selectRunPanel(first, 1, 'a', () => 'new');
}
function preflight(): SqlRunPreflight {
    const draft = complete();
    return { version: 1, source: draft.source, complete: true, removed_panel_ids: [],
        unresolved_statement_indexes: [], unresolved_panel_ids: [], statements: draft.statements.map((s, i) => ({
            ...s, statement_index: i, kind: 'keep', panel_id: i === 0 ? 'b' : 'a', creation_key: null,
        })) };
}

it('new queries get creation choices only after every old ID has been accounted for', () => {
    const projection = { source: '', statements: [{ statement_index: 0, panel_id: 'a' },
        { statement_index: 1, panel_id: null }], unresolved_panel_ids: ['b'] };
    expect(initialRunChoices(projection, () => 'new')).toEqual([{ kind: 'keep', statement_index: 0, panel_id: 'a' }]);
    expect(initialRunChoices({ ...projection, unresolved_panel_ids: [] }, () => 'new')).toHaveLength(2);
});

it('all existing identities require an explicit query and duplicates cannot steal another choice', () => {
    const draft = selectRunPanel(resolution(), 0, 'b', () => 'new');
    expect(runResolutionComplete(draft)).toBe(false);
    expect(() => selectRunPanel(draft, 1, 'b', () => 'new')).toThrow();
    expect(() => selectRunPanel(draft, 1, 'foreign', () => 'new')).toThrow();
    expect(runResolutionComplete(complete())).toBe(true);
    expect(runResolutionComplete(selectRunPanel(complete(), 0, null, () => 'new'))).toBe(false);
});

it('clearing a choice allows an explicit swap without silently reassigning another query', () => {
    const draft = selectRunPanel(complete(), 0, undefined, () => 'new');
    expect(draft.choices).toHaveLength(1);
    expect(complete().choices).toHaveLength(2);
});

it('requires explicit removal of unused panels and rejects contradictory removal choices', () => {
    const draft = selectRunPanel({ ...resolution(), statements: resolution().statements.slice(0, 1) }, 0, 'b', () => 'new');
    expect(runResolutionComplete(draft)).toBe(false);
    const removed = selectRunRemoval(draft, 'a', true);
    expect(runResolutionComplete(removed)).toBe(true);
    expect(runResolutionComplete(selectRunRemoval(removed, 'a', false))).toBe(false);
    expect(() => selectRunRemoval(draft, 'b', true)).toThrow();
    expect(() => selectRunRemoval(draft, 'foreign', true)).toThrow();
    expect(runResolutionComplete({ ...removed, choices: [...removed.choices, { kind: 'remove', panel_id: 'a' }] })).toBe(false);
    const plan = { ...preflight(), statements: preflight().statements.slice(0, 1), removed_panel_ids: ['a'] };
    expect(() => requireRunPreflight(plan, removed)).not.toThrow();
    expect(() => requireRunPreflight({ ...plan, removed_panel_ids: ['b'] }, removed)).toThrow();
});

it('can explicitly remove every panel from a script with no statements', () => {
    const draft = { ...resolution(), statements: [] };
    const removed = selectRunRemoval(selectRunRemoval(draft, 'a', true), 'b', true);
    expect(runResolutionComplete(removed)).toBe(true);
    expect(runResolutionComplete(draft)).toBe(false);
});

it('accepts a coherent server proposal including an explicit new panel', () => {
    expect(() => requireRunPreflight(preflight(), complete())).not.toThrow();
    const draft = { ...resolution(), panels: [] };
    const chosen = selectRunPanel(selectRunPanel(draft, 0, null, () => 'new-a'), 1, null, () => 'new-b');
    const plan = { ...preflight(), statements: preflight().statements.map((s, i) => ({ ...s, kind: 'create' as const,
        panel_id: null, creation_key: i === 0 ? 'new-a' : 'new-b' })) };
    expect(() => requireRunPreflight(plan, chosen)).not.toThrow();
});

it.each(['source', 'incomplete', 'removed', 'unresolved', 'count', 'index', 'identity', 'offset', 'sql', 'contradiction'])
('rejects a %s mismatch before mutation', field => {
    const plan = preflight();
    if (field === 'source') plan.source = 'SELECT 99';
    if (field === 'incomplete') plan.complete = false;
    if (field === 'removed') plan.removed_panel_ids = ['a'];
    if (field === 'unresolved') plan.unresolved_panel_ids = ['a'];
    if (field === 'count') plan.statements.pop();
    if (field === 'index') plan.statements[0].statement_index = 1;
    if (field === 'identity') plan.statements[0].panel_id = 'a';
    if (field === 'offset') plan.statements[0].start_offset = 1;
    if (field === 'sql') plan.statements[0].sql = 'SELECT 99';
    if (field === 'contradiction') plan.statements[0].creation_key = 'new';
    expect(() => requireRunPreflight(plan, complete())).toThrow();
});
