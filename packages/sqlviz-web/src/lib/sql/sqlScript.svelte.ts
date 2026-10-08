import { apiPost } from '$lib/api';

export type SqlStatement = { sql: string; start_offset: number; end_offset: number };
type SqlScriptResponse = { version: 1; dialect: 'duckdb'; statements: SqlStatement[] };
type Analysis = { source: string; statements: SqlStatement[] };

/** Transport, not a second SQL parser. Offsets use JavaScript's UTF-16 units. */
export async function parseSqlScript(source: string): Promise<SqlStatement[]> {
    const response = await apiPost<SqlScriptResponse>('/api/v1/sql/parse', { sql: source });
    return response.statements;
}

/** One-source cache and in-flight deduplication; late checks cannot replace newer ones. */
export function createSqlScriptAnalysis(parse = parseSqlScript) {
    let confirmed = $state<Analysis | null>(null);
    let failure = $state<{ source: string; message: string } | null>(null);
    let generation = 0;
    let inFlight: { source: string; promise: Promise<SqlStatement[]> } | null = null;

    function analyze(source: string): Promise<SqlStatement[]> {
        if (confirmed?.source === source) return Promise.resolve(confirmed.statements);
        if (inFlight?.source === source) return inFlight.promise;
        const request = ++generation;
        failure = null;
        const operation = source === '' ? Promise.resolve([]) : parse(source);
        const promise = operation.then(statements => {
            if (request === generation) confirmed = { source, statements };
            return statements;
        }).catch((error: unknown) => {
            if (request === generation) failure = {
                source, message: error instanceof Error ? error.message : 'SQL check failed. Retry.',
            };
            throw error;
        }).finally(() => {
            if (request === generation) inFlight = null;
        });
        inFlight = { source, promise };
        return promise;
    }

    return {
        analyze,
        get: (source: string) => confirmed?.source === source ? confirmed.statements : null,
        error: (source: string) => failure?.source === source ? failure.message : null,
    };
}

/** A separator on its own line cannot be swallowed by a trailing -- comment. */
export function joinSqlStatements(statements: string[]): string {
    return statements.join('\n;\n\n');
}
