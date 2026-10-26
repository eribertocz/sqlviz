/** Conditional SQL draft saves (S1.1c.2c.3c); the revision is expected state, not a credential. */

export const SQL_DRAFT_REVISION = /^sql-draft-v1:[0-9a-f]{64}$/;

export type SqlDraft = { version: 1; dashboard_id: string; source: string; revision: string; initialized: boolean };

export function draftPath(dashboardId: string): string {
    return `/api/v1/dashboards/${encodeURIComponent(dashboardId)}/sql-script/draft`;
}

/** Accept only a draft for the expected dashboard; never adopt a malformed revision. */
export function requireSqlDraft(value: unknown, dashboardId: string): SqlDraft {
    const draft = value as SqlDraft;
    if (!draft || typeof draft !== 'object' || draft.version !== 1 || draft.dashboard_id !== dashboardId ||
        typeof draft.source !== 'string' || typeof draft.revision !== 'string' ||
        !SQL_DRAFT_REVISION.test(draft.revision) || typeof draft.initialized !== 'boolean') {
        throw new Error('Could not verify the saved draft. Reload the dashboard.');
    }
    return draft;
}

/** Another writer saved first; the local text must be kept and reviewed, not overwritten. */
export function isDraftConflict(error: unknown): boolean {
    return !!error && typeof error === 'object' && 'code' in error && error.code === 'sql_draft_conflict';
}
