<script lang="ts">
    import type { FilterControl, FilterDomain } from '$lib/types';

    let { control, filterVals, domain, onChange }: {
        control: FilterControl;
        filterVals: Record<string, unknown>;
        domain?: FilterDomain;
        onChange: (varName: string, value: unknown) => void;
    } = $props();

    const vars = $derived(control.variable.split(',').map(v => v.trim()));

    // Convenience: for single-variable controls
    const currentVal = $derived(filterVals[vars[0]] ?? '');

    // For range controls: values for each half
    const rangeFrom = $derived(filterVals[vars[0]] ?? '');
    const rangeTo   = $derived(vars.length > 1 ? filterVals[vars[1]] ?? '' : '');

    // ── Domain-driven rich controls ──────────────────────────────────────────
    const options = $derived((domain?.values ?? []).map(v => String(v)));
    const hasOptions = $derived(options.length > 0);
    const hasRange = $derived(
        domain != null
        && typeof domain.min === 'number'
        && typeof domain.max === 'number'
        && domain.max > domain.min
    );
    // Integer columns step by 1; floats get fine-grained steps across the range.
    const isIntColumn = $derived(
        /INT|SERIAL|HUGEINT/i.test(control.column_type)
        && !/POINT/i.test(control.column_type)
    );
    const sliderStep = $derived(
        !hasRange ? 1
            : isIntColumn ? 1
                : Math.max((domain!.max! - domain!.min!) / 100, 0.0001)
    );

    const selectedArray = $derived(
        Array.isArray(filterVals[vars[0]]) ? (filterVals[vars[0]] as string[]) : []
    );

    // Slider positions default to the domain bounds until the user moves them.
    const sliderFrom = $derived(
        rangeFrom === '' ? (domain?.min ?? 0) : Number(rangeFrom)
    );
    const sliderTo = $derived(
        rangeTo === '' ? (domain?.max ?? 0) : Number(rangeTo)
    );

    function onSingle(e: Event) {
        onChange(vars[0], (e.target as HTMLInputElement).value);
    }

    function onSelect(e: Event) {
        onChange(vars[0], (e.target as HTMLSelectElement).value);
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

    function onToggleOption(opt: string, checked: boolean) {
        const next = checked
            ? [...selectedArray, opt]
            : selectedArray.filter(v => v !== opt);
        onChange(vars[0], next);
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

    // Clamp so the two slider handles can't cross over.
    function onSliderFrom(e: Event) {
        const v = Math.min(Number((e.target as HTMLInputElement).value), sliderTo);
        onChange(vars[0], v);
    }

    function onSliderTo(e: Event) {
        const v = Math.max(Number((e.target as HTMLInputElement).value), sliderFrom);
        onChange(vars[1], v);
    }

    const multiselectDisplay = $derived(
        Array.isArray(filterVals[vars[0]])
            ? (filterVals[vars[0]] as string[]).join(', ')
            : String(filterVals[vars[0]] ?? '')
    );

    const multiselectLabel = $derived(
        selectedArray.length === 0 ? 'Any' : `${selectedArray.length} selected`
    );
</script>

<div class="filter-control">
    <span class="filter-label">{control.label}</span>

    {#if control.control_type === 'dropdown'}
        {#if hasOptions}
            <select class="filter-input filter-select" value={currentVal as string} onchange={onSelect}>
                <option value="">All</option>
                {#each options as opt}
                    <option value={opt}>{opt}</option>
                {/each}
            </select>
        {:else}
            <input
                type="text"
                class="filter-input"
                value={currentVal as string}
                placeholder="value…"
                oninput={onSingle}
            />
        {/if}

    {:else if control.control_type === 'multiselect'}
        {#if hasOptions}
            <details class="multiselect">
                <summary class="filter-input multiselect-summary">{multiselectLabel}</summary>
                <div class="multiselect-panel">
                    {#each options as opt}
                        <label class="multiselect-option">
                            <input
                                type="checkbox"
                                checked={selectedArray.includes(opt)}
                                onchange={(e) => onToggleOption(opt, (e.target as HTMLInputElement).checked)}
                            />
                            <span>{opt}</span>
                        </label>
                    {/each}
                </div>
            </details>
        {:else}
            <input
                type="text"
                class="filter-input filter-input--wide"
                value={multiselectDisplay}
                placeholder="val1, val2…"
                oninput={onMultiselect}
            />
        {/if}

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
        {#if hasRange}
            <div class="slider-group">
                <span class="slider-val">{sliderFrom}</span>
                <div class="slider-track-wrap">
                    <input
                        type="range"
                        class="slider"
                        min={domain!.min!}
                        max={domain!.max!}
                        step={sliderStep}
                        value={sliderFrom}
                        oninput={onSliderFrom}
                        aria-label="{control.label} minimum"
                    />
                    <input
                        type="range"
                        class="slider"
                        min={domain!.min!}
                        max={domain!.max!}
                        step={sliderStep}
                        value={sliderTo}
                        oninput={onSliderTo}
                        aria-label="{control.label} maximum"
                    />
                </div>
                <span class="slider-val">{sliderTo}</span>
            </div>
        {:else}
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
        {/if}

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

    /* ── Native <select> dropdown ─────────────────────────────────────────── */
    .filter-select {
        cursor: pointer;
        padding-right: 0.25rem;
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

    /* ── Multiselect (checkbox disclosure) ────────────────────────────────── */
    .multiselect {
        position: relative;
    }

    .multiselect-summary {
        display: flex;
        align-items: center;
        min-width: 120px;
        cursor: pointer;
        list-style: none;
        user-select: none;
    }

    .multiselect-summary::-webkit-details-marker { display: none; }

    .multiselect-summary::after {
        content: '▾';
        margin-left: auto;
        padding-left: 0.5rem;
        color: var(--sqlviz-text-muted);
        font-size: 0.7rem;
    }

    .multiselect-panel {
        position: absolute;
        z-index: 20;
        top: calc(100% + 4px);
        left: 0;
        min-width: 100%;
        max-height: 240px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 0.125rem;
        padding: 0.375rem;
        background: var(--sqlviz-bg-surface);
        border: 1px solid var(--sqlviz-border);
        border-radius: var(--sqlviz-radius);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.18);
    }

    .multiselect-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0.375rem;
        font-size: 0.8125rem;
        color: var(--sqlviz-text);
        white-space: nowrap;
        cursor: pointer;
        border-radius: var(--sqlviz-radius);
    }

    .multiselect-option:hover {
        background: var(--sqlviz-bg);
    }

    /* ── Range slider (dual handle) ───────────────────────────────────────── */
    .slider-group {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .slider-val {
        font-size: 0.75rem;
        color: var(--sqlviz-text);
        font-variant-numeric: tabular-nums;
        min-width: 2ch;
        text-align: center;
    }

    .slider-track-wrap {
        position: relative;
        width: 120px;
        height: 20px;
        display: flex;
        align-items: center;
    }

    .slider {
        position: absolute;
        left: 0;
        width: 100%;
        margin: 0;
        background: transparent;
        pointer-events: none;
        -webkit-appearance: none;
        appearance: none;
    }

    /* Only the thumbs are interactive so both overlapping tracks stay usable. */
    .slider::-webkit-slider-thumb {
        pointer-events: auto;
        -webkit-appearance: none;
        appearance: none;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: var(--sqlviz-primary);
        border: 2px solid var(--sqlviz-bg-surface);
        cursor: pointer;
    }

    .slider::-moz-range-thumb {
        pointer-events: auto;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        background: var(--sqlviz-primary);
        border: 2px solid var(--sqlviz-bg-surface);
        cursor: pointer;
    }

    .slider::-webkit-slider-runnable-track {
        height: 3px;
        border-radius: 2px;
        background: var(--sqlviz-border);
    }

    .slider::-moz-range-track {
        height: 3px;
        border-radius: 2px;
        background: var(--sqlviz-border);
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
