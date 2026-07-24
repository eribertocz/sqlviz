<script lang="ts">
    import type { FilterControl, FilterDomain } from '$lib/types';
    import * as Select from '$lib/components/ui/select/index.js';
    import * as Popover from '$lib/components/ui/popover/index.js';
    import * as Command from '$lib/components/ui/command/index.js';
    import { Slider } from '$lib/components/ui/slider/index.js';
    import { Switch } from '$lib/components/ui/switch/index.js';
    import { Input } from '$lib/components/ui/input/index.js';
    import { Calendar } from '$lib/components/ui/calendar/index.js';
    import { RangeCalendar } from '$lib/components/ui/range-calendar/index.js';
    import { parseDate, type DateValue } from '@internationalized/date';
    import CheckIcon from '@lucide/svelte/icons/check';
    import CalendarIcon from '@lucide/svelte/icons/calendar';
    import ChevronsUpDownIcon from '@lucide/svelte/icons/chevrons-up-down';
    import XIcon from '@lucide/svelte/icons/x';

    let { control, filterVals, domain, onChange, pill = false }: {
        control: FilterControl;
        filterVals: Record<string, unknown>;
        domain?: FilterDomain;
        onChange: (varName: string, value: unknown) => void;
        /** Compact pill rendering for header filter chips. */
        pill?: boolean;
    } = $props();

    // Marker class appended to a control's trigger/input when rendered as a
    // header chip — the pill styles below neutralize the shadcn trigger frame
    // so the outer .filter-control.pill reads as one small pill.
    const chip = $derived(pill ? 'filter-chip-el' : '');

    // A pill reflects its state: ghost (dashed) when empty, accent when active.
    const hasValue = $derived.by(() => {
        if (control.control_type === 'multiselect') return selectedArray.length > 0;
        if (control.control_type === 'range_slider'
            || control.control_type === 'date_range_picker') {
            return rangeFrom !== '' || rangeTo !== '';
        }
        if (control.control_type === 'toggle') return !!currentVal;
        return currentVal !== '' && currentVal !== undefined && currentVal !== null;
    });

    const vars = $derived(control.variable.split(',').map(v => v.trim()));

    const currentVal = $derived(filterVals[vars[0]] ?? '');
    const rangeFrom  = $derived(filterVals[vars[0]] ?? '');
    const rangeTo    = $derived(vars.length > 1 ? filterVals[vars[1]] ?? '' : '');

    // ── Domain-driven options / bounds ───────────────────────────────────────
    const options = $derived((domain?.values ?? []).map(v => String(v)));
    const hasOptions = $derived(options.length > 0);
    const hasRange = $derived(
        domain != null
        && typeof domain.min === 'number'
        && typeof domain.max === 'number'
        && domain.max > domain.min
    );
    const isIntColumn = $derived(
        /INT|SERIAL|HUGEINT/i.test(control.column_type) && !/POINT/i.test(control.column_type)
    );
    const sliderStep = $derived(
        !hasRange ? 1 : isIntColumn ? 1 : Math.max((domain!.max! - domain!.min!) / 100, 0.0001)
    );

    const selectedArray = $derived(
        Array.isArray(filterVals[vars[0]]) ? (filterVals[vars[0]] as string[]) : []
    );

    const sliderValue = $derived<[number, number]>([
        rangeFrom === '' ? (domain?.min ?? 0) : Number(rangeFrom),
        rangeTo === '' ? (domain?.max ?? 0) : Number(rangeTo),
    ]);

    let comboOpen = $state(false);

    // ── Date <-> string helpers (@internationalized/date) ────────────────────
    function toDate(s: unknown): DateValue | undefined {
        if (typeof s !== 'string' || !s) return undefined;
        try { return parseDate(s); } catch { return undefined; }
    }
    const dateVal      = $derived(toDate(currentVal));
    const rangeDateVal = $derived({ start: toDate(rangeFrom), end: toDate(rangeTo) });

    // ── Emit helpers ─────────────────────────────────────────────────────────
    function onNumber(e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        onChange(vars[0], raw === '' ? '' : Number(raw));
    }
    function onSearch(e: Event) {
        onChange(vars[0], (e.target as HTMLInputElement).value);
    }
    function onRangeNum(idx: 0 | 1, e: Event) {
        const raw = (e.target as HTMLInputElement).value;
        onChange(vars[idx], raw === '' ? '' : Number(raw));
    }
    function onMultiselectText(e: Event) {
        const arr = (e.target as HTMLInputElement).value
            .split(',').map(v => v.trim()).filter(Boolean);
        onChange(vars[0], arr);
    }
    function toggleOption(opt: string) {
        const next = selectedArray.includes(opt)
            ? selectedArray.filter(v => v !== opt)
            : [...selectedArray, opt];
        onChange(vars[0], next);
    }
    function onSliderChange(v: number[]) {
        onChange(vars[0], v[0]);
        onChange(vars[1], v[1]);
    }
    function onDate(v: DateValue | undefined) {
        onChange(vars[0], v ? v.toString() : '');
    }
    function onDateRange(v: { start?: DateValue; end?: DateValue } | undefined) {
        onChange(vars[0], v?.start ? v.start.toString() : '');
        onChange(vars[1], v?.end ? v.end.toString() : '');
    }

    const comboLabel = $derived(
        selectedArray.length === 0 ? 'Any' : `${selectedArray.length} selected`
    );
    const dateLabel = $derived(typeof currentVal === 'string' && currentVal ? currentVal : 'Pick a date');
    const rangeLabel = $derived(
        rangeFrom || rangeTo ? `${rangeFrom || '…'} – ${rangeTo || '…'}` : 'Pick a range'
    );
</script>

<div class="filter-control" class:pill class:active={pill && hasValue}>
    <span class="filter-label">{control.label}</span>

    {#if control.control_type === 'dropdown'}
        {#if hasOptions}
            <Select.Root type="single" value={currentVal as string}
                onValueChange={(v) => onChange(vars[0], v === '__clear__' ? '' : (v ?? ''))}>
                <Select.Trigger class="h-7 min-w-[120px] text-xs {chip}">
                    {#if currentVal}
                        {String(currentVal)}
                    {:else}
                        <span class="filter-placeholder">Select…</span>
                    {/if}
                </Select.Trigger>
                <Select.Content>
                    <!-- Empty state = "no filter". The clear action lives inside
                         the dropdown so the header pill stays clean (no × chip). -->
                    {#if currentVal}
                        <Select.Item value="__clear__" label="Clear filter">
                            <XIcon class="mr-1 size-3.5" /> Clear filter
                        </Select.Item>
                        <Select.Separator />
                    {/if}
                    {#each options as opt}
                        <Select.Item value={opt} label={opt}>{opt}</Select.Item>
                    {/each}
                </Select.Content>
            </Select.Root>
            {#if currentVal && !pill}
                <button type="button" class="filter-clear" title="Clear filter"
                    aria-label="Clear filter" onclick={() => onChange(vars[0], '')}>
                    <XIcon class="size-3" />
                </button>
            {/if}
        {:else}
            <Input type="text" class="h-7 w-[140px] text-xs {chip}" placeholder="value…"
                value={currentVal as string} oninput={onSearch} />
        {/if}

    {:else if control.control_type === 'multiselect'}
        {#if hasOptions}
            <Popover.Root bind:open={comboOpen}>
                <Popover.Trigger class="inline-flex h-7 min-w-[140px] items-center justify-between rounded-md border border-input bg-transparent px-2.5 text-xs {chip}">
                    {comboLabel}
                    <ChevronsUpDownIcon class="ml-2 size-3 opacity-50" />
                </Popover.Trigger>
                <Popover.Content class="w-[220px] p-0" align="start">
                    <Command.Root>
                        <Command.Input placeholder="Search…" class="h-8 text-xs" />
                        <Command.List>
                            <Command.Empty>No results.</Command.Empty>
                            <Command.Group>
                                {#each options as opt}
                                    <Command.Item value={opt} onSelect={() => toggleOption(opt)}>
                                        <CheckIcon class={`mr-2 size-4 ${selectedArray.includes(opt) ? 'opacity-100' : 'opacity-0'}`} />
                                        {opt}
                                    </Command.Item>
                                {/each}
                            </Command.Group>
                        </Command.List>
                    </Command.Root>
                </Popover.Content>
            </Popover.Root>
        {:else}
            <Input type="text" class="h-7 w-[160px] text-xs {chip}" placeholder="val1, val2…"
                value={selectedArray.join(', ')} oninput={onMultiselectText} />
        {/if}

    {:else if control.control_type === 'date_picker'}
        <Popover.Root>
            <Popover.Trigger class="inline-flex h-7 min-w-[140px] items-center justify-between rounded-md border border-input bg-transparent px-2.5 text-xs {chip}">
                {dateLabel}
                <CalendarIcon class="ml-2 size-3 opacity-50" />
            </Popover.Trigger>
            <Popover.Content class="w-auto p-0" align="start">
                <Calendar type="single" value={dateVal} onValueChange={onDate} />
            </Popover.Content>
        </Popover.Root>

    {:else if control.control_type === 'date_range_picker'}
        <Popover.Root>
            <Popover.Trigger class="inline-flex h-7 min-w-[170px] items-center justify-between rounded-md border border-input bg-transparent px-2.5 text-xs {chip}">
                {rangeLabel}
                <CalendarIcon class="ml-2 size-3 opacity-50" />
            </Popover.Trigger>
            <Popover.Content class="w-auto p-0" align="start">
                <RangeCalendar
                    value={rangeDateVal as never}
                    onValueChange={(v) => onDateRange(v as never)}
                />
            </Popover.Content>
        </Popover.Root>

    {:else if control.control_type === 'numeric'}
        <Input type="number" class="h-7 w-[90px] text-xs {chip}" placeholder="0"
            value={currentVal as number} oninput={onNumber} />

    {:else if control.control_type === 'range_slider'}
        {#if hasRange}
            <div class="slider-group">
                <span class="slider-val">{sliderValue[0]}</span>
                <Slider type="multiple" value={sliderValue} onValueChange={onSliderChange}
                    min={domain!.min!} max={domain!.max!} step={sliderStep} class="w-[120px]" />
                <span class="slider-val">{sliderValue[1]}</span>
            </div>
        {:else}
            <div class="slider-group">
                <Input type="number" class="h-7 w-[72px] text-xs" placeholder="min"
                    value={rangeFrom as number} oninput={(e) => onRangeNum(0, e)} />
                <span class="range-sep">–</span>
                <Input type="number" class="h-7 w-[72px] text-xs" placeholder="max"
                    value={rangeTo as number} oninput={(e) => onRangeNum(1, e)} />
            </div>
        {/if}

    {:else if control.control_type === 'search'}
        <Input type="text" class="h-7 w-[160px] text-xs {chip}" placeholder="%keyword%"
            value={currentVal as string} oninput={onSearch} />

    {:else if control.control_type === 'toggle'}
        <Switch checked={!!currentVal} onCheckedChange={(v) => onChange(vars[0], v)} />
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

    .range-sep {
        color: var(--sqlviz-text-muted);
        font-size: 0.75rem;
        flex-shrink: 0;
    }

    .filter-placeholder {
        color: var(--sqlviz-text-muted);
    }

    .filter-clear {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        height: 1.75rem;
        width: 1.75rem;
        border: 1px solid transparent;
        border-radius: 0.375rem;
        color: var(--sqlviz-text-muted);
        background: transparent;
        cursor: pointer;
        flex-shrink: 0;
        transition: color 0.12s ease, background 0.12s ease;
    }

    .filter-clear:hover {
        color: var(--sqlviz-text);
        background: rgba(127, 127, 127, 0.12);
    }

    /* ── Header chip (pill) rendering ─────────────────────────────────────── */
    /* Empty = ghost (dashed, muted); active = accent (solid, tinted). */
    .filter-control.pill {
        gap: 0.375rem;
        padding: 3px 10px;
        border: 1px dashed var(--sqlviz-border);
        border-radius: 100px;
        background: transparent;
        font-size: 11px;
        line-height: 1.4;
        cursor: pointer;
        transition: border-color 0.12s ease, background 0.12s ease, color 0.12s ease;
    }
    .filter-control.pill:hover { border-color: var(--sqlviz-primary); }

    .filter-control.pill.active {
        border-style: solid;
        border-color: color-mix(in srgb, var(--sqlviz-primary) 45%, var(--sqlviz-border));
        background: color-mix(in srgb, var(--sqlviz-primary) 10%, transparent);
    }
    .filter-control.pill.active .filter-label { color: var(--sqlviz-primary); }

    .filter-control.pill .filter-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: none;
        letter-spacing: 0;
    }

    /* Neutralize the shadcn trigger/input frame so the outer pill is the only
       visible chrome; the trigger itself still opens its control on click. */
    .filter-control.pill :global(.filter-chip-el) {
        height: auto !important;
        min-height: 0 !important;
        min-width: 0 !important;
        width: auto !important;
        padding: 0 !important;
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        border-radius: 100px !important;
        font-size: 11px !important;
        color: var(--sqlviz-text);
        gap: 0.25rem !important;
    }
    .filter-control.pill :global(.filter-chip-el:focus-visible) {
        outline: none;
        box-shadow: none !important;
    }
    /* Shrink the caret / calendar glyphs to match the 11px chip. */
    .filter-control.pill :global(.filter-chip-el svg) {
        width: 12px !important;
        height: 12px !important;
        opacity: 0.6;
    }
</style>
