<script lang="ts">
    import type { FilterControl } from '$lib/types';

    let { control, filterVals, onChange }: {
        control: FilterControl;
        filterVals: Record<string, unknown>;
        onChange: (varName: string, value: unknown) => void;
    } = $props();

    const vars = $derived(control.variable.split(',').map(v => v.trim()));

    // Convenience: for single-variable controls
    const currentVal = $derived(filterVals[vars[0]] ?? '');

    // For range controls: values for each half
    const rangeFrom = $derived(filterVals[vars[0]] ?? '');
    const rangeTo   = $derived(vars.length > 1 ? filterVals[vars[1]] ?? '' : '');

    function onSingle(e: Event) {
        onChange(vars[0], (e.target as HTMLInputElement).value);
    }

    function onNumber(e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        onChange(vars[0], raw === '' ? '' : Number(raw));
    }

    function onMultiselect(e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        const arr = raw.split(',').map(v => v.trim()).filter(Boolean);
        onChange(vars[0], arr);
    }

    function onToggle(e: Event) {
        onChange(vars[0], (e.target as HTMLInputElement).checked);
    }

    function onRangeFrom(e: Event) {
        onChange(vars[0], (e.target as HTMLInputElement).value);
    }

    function onRangeTo(e: Event) {
        onChange(vars[1], (e.target as HTMLInputElement).value);
    }

    function onRangeFromNum(e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        onChange(vars[0], raw === '' ? '' : Number(raw));
    }

    function onRangeToNum(e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        onChange(vars[1], raw === '' ? '' : Number(raw));
    }

    const multiselectDisplay = $derived(
        Array.isArray(filterVals[vars[0]])
            ? (filterVals[vars[0]] as string[]).join(', ')
            : String(filterVals[vars[0]] ?? '')
    );
</script>

<div class="filter-control">
    <span class="filter-label">{control.label}</span>

    {#if control.control_type === 'dropdown'}
        <input
            type="text"
            class="filter-input"
            value={currentVal as string}
            placeholder="value…"
            oninput={onSingle}
        />

    {:else if control.control_type === 'multiselect'}
        <input
            type="text"
            class="filter-input filter-input--wide"
            value={multiselectDisplay}
            placeholder="val1, val2…"
            oninput={onMultiselect}
        />

    {:else if control.control_type === 'date_picker'}
        <input
            type="date"
            class="filter-input"
            value={currentVal as string}
            onchange={onSingle}
        />

    {:else if control.control_type === 'date_range_picker'}
        <div class="range-group">
            <input
                type="date"
                class="filter-input"
                value={rangeFrom as string}
                onchange={onRangeFrom}
            />
            <span class="range-sep">–</span>
            <input
                type="date"
                class="filter-input"
                value={rangeTo as string}
                onchange={onRangeTo}
            />
        </div>

    {:else if control.control_type === 'numeric'}
        <input
            type="number"
            class="filter-input filter-input--narrow"
            value={currentVal as number}
            placeholder="0"
            oninput={onNumber}
        />

    {:else if control.control_type === 'range_slider'}
        <div class="range-group">
            <input
                type="number"
                class="filter-input filter-input--narrow"
                value={rangeFrom as number}
                placeholder="min"
                oninput={onRangeFromNum}
            />
            <span class="range-sep">–</span>
            <input
                type="number"
                class="filter-input filter-input--narrow"
                value={rangeTo as number}
                placeholder="max"
                oninput={onRangeToNum}
            />
        </div>

    {:else if control.control_type === 'search'}
        <input
            type="text"
            class="filter-input filter-input--wide"
            value={currentVal as string}
            placeholder="%keyword%"
            oninput={onSingle}
        />

    {:else if control.control_type === 'toggle'}
        <label class="toggle-label">
            <input
                type="checkbox"
                class="toggle-input"
                checked={!!currentVal}
                onchange={onToggle}
            />
            <span class="toggle-track">
                <span class="toggle-thumb"></span>
            </span>
        </label>
    {/if}
</div>

<style>
    .filter-control {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-shrink: 0;
    }

    .filter-label {
        font-size: 0.6875rem;
        font-weight: 600;
        color: var(--sqlviz-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        white-space: nowrap;
    }

    .filter-input {
        height: 28px;
        padding: 0 0.5rem;
        background: var(--sqlviz-bg);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        color: var(--sqlviz-text);
        font-size: 0.8125rem;
        font-family: var(--sqlviz-font-sans);
        outline: none;
        min-width: 120px;
        transition: border-color 0.15s;
    }

    .filter-input:focus {
        border-color: var(--sqlviz-primary);
    }

    /* date inputs need explicit width because browsers vary */
    input[type="date"].filter-input {
        min-width: 130px;
    }

    .filter-input--narrow {
        min-width: 72px;
    }

    .filter-input--wide {
        min-width: 160px;
    }

    .range-group {
        display: flex;
        align-items: center;
        gap: 0.375rem;
    }

    .range-sep {
        color: var(--sqlviz-text-muted);
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    /* ── Toggle ───────────────────────────────────────────── */
    .toggle-label {
        display: flex;
        align-items: center;
        cursor: pointer;
        gap: 0.375rem;
    }

    .toggle-input {
        display: none;
    }

    .toggle-track {
        width: 32px;
        height: 18px;
        background: var(--sqlviz-border);
        border-radius: 9px;
        position: relative;
        transition: background 0.2s;
        flex-shrink: 0;
    }

    .toggle-input:checked + .toggle-track {
        background: var(--sqlviz-primary);
    }

    .toggle-thumb {
        position: absolute;
        top: 2px;
        left: 2px;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: #fff;
        transition: transform 0.2s;
    }

    .toggle-input:checked + .toggle-track .toggle-thumb {
        transform: translateX(14px);
    }
</style>
