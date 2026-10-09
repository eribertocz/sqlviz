import type { SqlStatement } from './sqlScript.svelte';
import type { SqlIdentityProjection } from './sqlIdentityDraft';

export type SqlRunChoice = { kind: 'keep'; statement_index: number; panel_id: string }
    | { kind: 'create'; statement_index: number; creation_key: string };
export type SqlRunResolution = {
    source: string;
    statements: readonly SqlStatement[];
    panels: readonly { id: string; label: string; sql: string }[];
    choices: readonly SqlRunChoice[];
};
export type SqlRunPreflight = {
    version: 1; source: string; complete: boolean;
    statements: (SqlStatement & { statement_index: number; kind: 'keep' | 'create';
        panel_id: string | null; creation_key: string | null })[];
    removed_panel_ids: string[]; unresolved_statement_indexes: number[]; unresolved_panel_ids: string[];
};

/** Defaults create new panels only when every old identity has already been accounted for. */
export function initialRunChoices(projection: SqlIdentityProjection, newKey: () => string): SqlRunChoice[] {
    return projection.statements.flatMap<SqlRunChoice>(item => item.panel_id
        ? [{ kind: 'keep', statement_index: item.statement_index, panel_id: item.panel_id }]
        : projection.unresolved_panel_ids.length === 0
            ? [{ kind: 'create', statement_index: item.statement_index, creation_key: newKey() }] : []);
}

export function runResolutionComplete(resolution: SqlRunResolution): boolean {
    const indexes = new Set(resolution.choices.map(item => item.statement_index));
    const kept = resolution.choices.filter(item => item.kind === 'keep').map(item => item.panel_id);
    const available = new Set(resolution.panels.map(panel => panel.id));
    const keys = resolution.choices.filter(item => item.kind === 'create').map(item => item.creation_key);
    return resolution.choices.length === resolution.statements.length && indexes.size === resolution.statements.length
        && resolution.choices.every(item => Number.isInteger(item.statement_index) && item.statement_index >= 0
            && item.statement_index < resolution.statements.length)
        && new Set(kept).size === kept.length && kept.every(id => available.has(id)) && kept.length === available.size
        && keys.every(key => !!key) && new Set(keys).size === keys.length;
}

/** Replace one explicit choice; never silently move an ID selected by another query. */
export function selectRunPanel(resolution: SqlRunResolution, index: number,
    panelId: string | null | undefined, newKey: () => string): SqlRunResolution {
    if (!Number.isInteger(index) || index < 0 || index >= resolution.statements.length) throw new Error('Unknown query');
    if (panelId === undefined) return { ...resolution, choices: resolution.choices.filter(item => item.statement_index !== index) };
    if (panelId !== null && (!resolution.panels.some(panel => panel.id === panelId) ||
        resolution.choices.some(item => item.kind === 'keep' && item.panel_id === panelId && item.statement_index !== index))) {
        throw new Error('This panel is unavailable or already assigned');
    }
    const choice: SqlRunChoice = panelId === null
        ? { kind: 'create', statement_index: index, creation_key: newKey() }
        : { kind: 'keep', statement_index: index, panel_id: panelId };
    return { ...resolution, choices: [...resolution.choices.filter(item => item.statement_index !== index), choice] };
}

/** Refuse partial, reordered, stale or contradictory server proposals before any writes. */
export function requireRunPreflight(plan: SqlRunPreflight, resolution: SqlRunResolution): void {
    if (!runResolutionComplete(resolution) || plan.version !== 1 || plan.source !== resolution.source || !plan.complete ||
        plan.removed_panel_ids.length || plan.unresolved_panel_ids.length || plan.unresolved_statement_indexes.length ||
        plan.statements.length !== resolution.statements.length) throw new Error('Query associations need confirmation.');
    for (const [index, item] of plan.statements.entries()) {
        const statement = resolution.statements[index];
        const choice = resolution.choices.find(choice => choice.statement_index === index);
        if (item.statement_index !== index || item.sql !== statement.sql || item.start_offset !== statement.start_offset ||
            item.end_offset !== statement.end_offset || !choice || item.kind !== choice.kind ||
            (choice.kind === 'keep' ? item.panel_id !== choice.panel_id || item.creation_key !== null
                : item.creation_key !== choice.creation_key || item.panel_id !== null)) {
            throw new Error('SQL preflight no longer matches this draft. Retry.');
        }
    }
}
