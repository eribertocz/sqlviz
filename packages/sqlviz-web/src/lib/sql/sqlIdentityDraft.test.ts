import { expect, it } from 'vitest';
import { confirmedSqlDraft, editSqlIdentityDraft, projectSqlIdentity, settleSqlIdentityDraft,
    sqlDraftFromPanels, unboundSqlDraft, type SqlEditorChange, type SqlIdentityDraft, type SqlTextEdit } from './sqlIdentityDraft';

const first = 'SELECT 10';
const second = 'SELECT 20';
function baseline() {
    return sqlDraftFromPanels([{ id: 'a', sql_content: first }, { id: 'b', sql_content: second }]);
}
function statement(source: string, text: string, start = source.indexOf(text)) {
    return { sql: text, start_offset: start, end_offset: start + text.length };
}
function change(draft: SqlIdentityDraft, edits: readonly SqlTextEdit[]) {
    let after = draft.source;
    for (const edit of [...edits].sort((a, b) => b.rangeOffset - a.rangeOffset)) {
        after = after.slice(0, edit.rangeOffset) + edit.text + after.slice(edit.rangeOffset + edit.rangeLength);
    }
    return editSqlIdentityDraft(draft, { before: draft.source, after, changes: edits, isFlush: false });
}
function owners(draft: SqlIdentityDraft, fragments: string[]) {
    let offset = 0;
    const parsed = fragments.map(text => {
        const start = draft.source.indexOf(text, offset); offset = start + text.length;
        return statement(draft.source, text, start);
    });
    return projectSqlIdentity(draft, parsed);
}

it('interior edits retain ownership even when SQL becomes identical to another panel', () => {
    const draft = change(baseline(), [{ rangeOffset: 7, rangeLength: 1, text: '2' }]);
    expect(owners(draft, [second, second]).statements.map(item => item.panel_id)).toEqual(['a', 'b']);
    expect(baseline().source).toBe(`${first}\n;\n\n${second}`);
});

it('simultaneous edits use original offsets independently of event order', () => {
    const initial = baseline();
    const edits = [{ rangeOffset: initial.bindings[1].end_offset - 1, rangeLength: 1, text: '100' },
        { rangeOffset: 7, rangeLength: 1, text: '9' }];
    const draft = change(initial, edits);
    expect(draft).toEqual(change(initial, [...edits].reverse()));
    expect(owners(draft, ['SELECT 90', 'SELECT 2100']).statements.map(item => item.panel_id)).toEqual(['a', 'b']);
});

it('inserting a new query before a known block shifts it without stealing its ID', () => {
    const initial = baseline();
    const draft = change(initial, [{ rangeOffset: initial.bindings[1].start_offset, rangeLength: 0, text: 'SELECT 30\n;\n\n' }]);
    const projection = owners(draft, [first, 'SELECT 30', second]);
    expect(projection.statements.map(item => item.panel_id)).toEqual(['a', null, 'b']);
    expect(projection.unresolved_panel_ids).toEqual([]);
});

it('deleting a block leaves its panel pending rather than proposing an implicit deletion', () => {
    const draft = change(baseline(), [{ rangeOffset: 0, rangeLength: first.length, text: '' }]);
    const projection = owners(draft, [second]);
    expect(projection.statements[0].panel_id).toBe('b');
    expect(projection.unresolved_panel_ids).toEqual(['a']);
});

it('a full replacement or opaque reorder cannot transfer identities by index or SQL equality', () => {
    const initial = baseline();
    const reversed = `${second}\n;\n\n${first}`;
    const draft = change(initial, [{ rangeOffset: 0, rangeLength: initial.source.length, text: reversed }]);
    expect(owners(draft, [second, first]).statements.map(item => item.panel_id)).toEqual([null, null]);
    expect(owners(unboundSqlDraft(initial.source, initial.panel_ids), [first, second]).unresolved_panel_ids).toEqual(['a', 'b']);
});

it('crossing a statement boundary invalidates both touched bindings', () => {
    const initial = baseline();
    const start = initial.bindings[0].end_offset - 1;
    const end = initial.bindings[1].start_offset + 1;
    const draft = change(initial, [{ rangeOffset: start, rangeLength: end - start, text: 'x' }]);
    expect(draft.bindings).toEqual([]);
});

it('split and merged statements require new decisions after native parsing', () => {
    const original = sqlDraftFromPanels([{ id: 'a', sql_content: first }]);
    const split = change(original, [{ rangeOffset: 8, rangeLength: 0, text: '; SELECT 2' }]);
    const parsed = [statement(split.source, 'SELECT 1'), statement(split.source, second)];
    expect(projectSqlIdentity(split, parsed).statements.map(item => item.panel_id)).toEqual([null, null]);
    const settled = settleSqlIdentityDraft(split, parsed);
    const restored = change(settled, [{ rangeOffset: 0, rangeLength: split.source.length, text: first }]);
    expect(owners(restored, [first]).statements[0].panel_id).toBeNull();

    const initial = baseline();
    const merged = change(initial, [{ rangeOffset: first.length, rangeLength: 4, text: ' UNION ALL ' }]);
    expect(owners(merged, [merged.source]).unresolved_panel_ids).toEqual(['a', 'b']);
});

it('boundary insertions are outside ownership; appending SQL is not guessed as a panel edit', () => {
    const initial = sqlDraftFromPanels([{ id: 'a', sql_content: first }]);
    const draft = change(initial, [{ rangeOffset: first.length, rangeLength: 0, text: ' AS total' }]);
    expect(owners(draft, [draft.source]).statements[0].panel_id).toBeNull();
});

it('uses UTF-16 offsets for emoji and preserves IDs without splitting literal semicolons', () => {
    const sql = "SELECT '\u{1f680};a'";
    const initial = sqlDraftFromPanels([{ id: 'a', sql_content: sql }, { id: 'b', sql_content: second }]);
    const draft = change(initial, [{ rangeOffset: sql.indexOf('a'), rangeLength: 1, text: 'long' }]);
    expect(owners(draft, ["SELECT '\u{1f680};long'", second]).statements.map(item => item.panel_id)).toEqual(['a', 'b']);
    expect(draft.bindings[1].start_offset).toBe(sql.length + 7);
});

it('allows native parsing to omit delimiter trivia within a constructed block', () => {
    const initial = sqlDraftFromPanels([{ id: 'a', sql_content: ' SELECT 10; ' }, { id: 'b', sql_content: second }]);
    expect(owners(initial, [first, second]).statements.map(item => item.panel_id)).toEqual(['a', 'b']);
    expect(sqlDraftFromPanels([{ id: 'a', sql_content: '' }, { id: 'b', sql_content: second }]).source).toBe(`\n;\n\n${second}`);
});

it('takes confirmed execution assignments explicitly, including identical SQL', () => {
    const source = `${first}; ${first}`;
    const draft = confirmedSqlDraft(source, [{ panel_id: 'b', statement: statement(source, first, 0) },
        { panel_id: 'a', statement: statement(source, first, first.length + 2) }]);
    expect(owners(draft, [first, first]).statements.map(item => item.panel_id)).toEqual(['b', 'a']);
    expect(() => confirmedSqlDraft(source, [{ panel_id: 'a', statement: statement(source, first, 0) },
        { panel_id: 'a', statement: statement(source, first, first.length + 2) }])).toThrow();
});

it.each([
    { before: 'old model' }, { isFlush: true },
    { changes: [{ rangeOffset: -1, rangeLength: 0, text: '' }] },
    { changes: [{ rangeOffset: 0, rangeLength: NaN, text: '' }] },
    { changes: [{ rangeOffset: 0, rangeLength: 999, text: '' }] },
    { changes: [{ rangeOffset: 0, rangeLength: 0, text: 'x' }, { rangeOffset: 0, rangeLength: 0, text: 'y' }] },
    { changes: [{ rangeOffset: 0, rangeLength: 5, text: '' }, { rangeOffset: 3, rangeLength: 1, text: '' }] },
    { after: 'unexplained source' },
    { changes: Array.from({ length: 1025 }, () => ({ rangeOffset: 0, rangeLength: 0, text: '' })) },
])('invalid or flushed change loses evidence instead of fabricating ownership (%j)', override => {
    const initial = baseline();
    const event: SqlEditorChange = { before: initial.source, after: initial.source, changes: [], isFlush: false, ...override };
    const draft = editSqlIdentityDraft(initial, event);
    expect(draft.bindings).toEqual([]); expect(draft.panel_ids).toEqual(['a', 'b']);
});

it('rejects stale parsing and keeps immutable snapshots detached from caller objects', () => {
    const assignment = { panel_id: 'a', statement: statement(first, first) };
    const draft = confirmedSqlDraft(first, [assignment]); assignment.panel_id = 'b';
    expect(draft.panel_ids).toEqual(['a']);
    expect(Object.isFrozen(draft.bindings[0])).toBe(true);
    expect(() => projectSqlIdentity(draft, [statement(first, second, 0)])).toThrow();
    expect(() => unboundSqlDraft('', Array.from({ length: 257 }, (_, i) => String(i)))).toThrow();
});
