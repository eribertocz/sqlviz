<script lang="ts">
    // SQLviz brand mark — three ascending bars in the primary colour. Sized via
    // the `size` prop; colour inherits from the `.brand-mark` currentColor.
    let { size = 18 }: { size?: number } = $props();
</script>

<span class="brand-mark" style="width:{size}px;height:{size}px" aria-hidden="true">
    <svg viewBox="0 0 24 24" width={size} height={size} fill="none">
        <rect x="3"  y="12" width="4" height="8"  rx="1.2" fill="currentColor" />
        <rect x="10" y="7"  width="4" height="13" rx="1.2" fill="currentColor" />
        <rect x="17" y="3"  width="4" height="17" rx="1.2" fill="currentColor" />
    </svg>
</span>

<style>
    .brand-mark {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        color: var(--sqlviz-primary);
        flex-shrink: 0;
    }
</style>
