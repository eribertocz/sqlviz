import { writable } from 'svelte/store';
import type { InferenceResult } from '$lib/types';

export interface ExplainTarget {
    panel_id: string;
    inference_result: InferenceResult;
    data: Record<string, unknown>[];
}

/** Set to open the explainability drawer; null to close it. */
export const explainTarget = writable<ExplainTarget | null>(null);
