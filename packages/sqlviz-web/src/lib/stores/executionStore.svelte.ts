/** Silent draft auto-save status shown as a subtle header indicator. */
export type SaveStatus = 'idle' | 'draft' | 'saving' | 'saved';

function createExecutionStore() {
    let executing = $state(false);
    let statusMsg = $state<string | null>(null);
    let errorMsg  = $state<string | null>(null);
    let saveStatus = $state<SaveStatus>('idle');

    return {
        get executing() { return executing; },
        set executing(v: boolean) { executing = v; },
        get statusMsg() { return statusMsg; },
        set statusMsg(v: string | null) { statusMsg = v; },
        get errorMsg() { return errorMsg; },
        set errorMsg(v: string | null) { errorMsg = v; },
        get saveStatus() { return saveStatus; },
        set saveStatus(v: SaveStatus) { saveStatus = v; },
    };
}

export const executionStore = createExecutionStore();
