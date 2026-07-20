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

    let { control, filterVals, domain, onChange }: {
        control: FilterControl;
        filterVals: Record<string, unknown>;
        domain?: FilterDomain;
        onChange: (varName: string, value: unknown) => void;
    } = $props();

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

<div class="filter-control">
    <span class="filter-label">{control.label}</span>

    {#if control.control_type === 'dropdown'}
        {#if hasOptions}
            <Select.Root type="single" value={currentVal as string}
                onValueChange={(v) => onChange(vars[0], v ?? '')}>
                <Select.Trigger class="h-7 min-w-[120px] text-xs">
                    {#if currentVal}
                        {String(currentVal)}
                    {:else}
                        <span class="filter-placeholder">Select…</span>
                    {/if}
                </Select.Trigger>
                <Select.Content>
                    {#each options as opt}
                        <Select.Item value={opt} label={opt}>{opt}</Select.Item>
                    {/each}
                </Select.Content>
            </Select.Root>
            {#if currentVal}
                <!-- Empty state = "no filter". Clearing removes the filter so
                     all rows show again (backend treats empty as "All"). -->
                <button type="button" class="filter-clear" title="Clear filter"
                    aria-label="Clear filter" onclick={() => onChange(vars[0], '')}>
                    <XIcon class="size-3" />
                </button>
            {/if}
        {:else}
            <Input type="text" class="h-7 w-[140px] text-xs" placeholder="value…"
                value={currentVal as string} oninput={onSearch} />
        {/if}

    {:else if control.control_type === 'multiselect'}
        {#if hasOptions}
            <Popover.Root bind:open={comboOpen}>
                <Popover.Trigger class="inline-flex h-7 min-w-[140px] items-center justify-between rounded-md border border-input bg-transparent px-2.5 text-xs">
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
            <Input type="text" class="h-7 w-[160px] text-xs" placeholder="val1, val2…"
                value={selectedArray.join(', ')} oninput={onMultiselectText} />
        {/if}

    {:else if control.control_type === 'date_picker'}
        <Popover.Root>
            <Popover.Trigger class="inline-flex h-7 min-w-[140px] items-center justify-between rounded-md border border-input bg-transparent px-2.5 text-xs">
                {dateLabel}
                <CalendarIcon class="ml-2 size-3 opacity-50" />
            </Popover.Trigger>
            <Popover.Content class="w-auto p-0" align="start">
                <Calendar type="single" value={dateVal} onValueChange={onDate} />
            </Popover.Content>
        </Popover.Root>

    {:else if control.control_type === 'date_range_picker'}
        <Popover.Root>
            <Popover.Trigger class="inline-flex h-7 min-w-[170px] items-center justify-between rounded-md border border-input bg-transparent px-2.5 text-xs">
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
        <Input type="number" class="h-7 w-[90px] text-xs" placeholder="0"
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
        <Input type="text" class="h-7 w-[160px] text-xs" placeholder="%keyword%"
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
</style>
