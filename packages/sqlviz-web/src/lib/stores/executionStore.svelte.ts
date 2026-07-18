function createExecutionStore() {
    let executing = $state(false);
    let statusMsg = $state<string | null>(null);
    let errorMsg  = $state<string | null>(null);

    return {
        get executing() { return executing; },
        set executing(v: boolean) { executing = v; },
        get statusMsg() { return statusMsg; },
        set statusMsg(v: string | null) { statusMsg = v; },
        get errorMsg() { return errorMsg; },
        set errorMsg(v: string | null) { errorMsg = v; },
    };
}

export const executionStore = createExecutionStore();
