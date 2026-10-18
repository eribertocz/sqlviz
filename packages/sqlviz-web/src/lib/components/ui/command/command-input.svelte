<script lang="ts">
	import { Command as CommandPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import * as InputGroup from "$lib/components/ui/input-group/index.js";
	import SearchIcon from '@lucide/svelte/icons/search';

	let {
		ref = $bindable(null),
		class: className,
		value = $bindable(""),
		...restProps
	}: CommandPrimitive.InputProps = $props();
</script>

<div data-slot="command-input-wrapper" class="command-search p-1 pb-0">
	<InputGroup.Root class="bg-input/30 border-input/30 h-8! rounded-lg! shadow-none *:data-[slot=input-group-addon]:pl-2!">
		<CommandPrimitive.Input
			{value}
			data-slot="command-input"
			class={cn(
				"h-full w-full min-w-0 text-sm outline-hidden disabled:cursor-not-allowed disabled:opacity-50",
				className
			)}
			{...restProps}
		>
			{#snippet child({ props })}
				<InputGroup.Input {...props} bind:value bind:ref />
			{/snippet}
		</CommandPrimitive.Input>
		<InputGroup.Addon>
			<SearchIcon class="size-4 shrink-0 opacity-50" />
		</InputGroup.Addon>
	</InputGroup.Root>
</div>

<style>
	/* The icon and input form one field; draw its focus on the rounded group. */
	.command-search :global([data-slot="command-input"]:focus-visible) {
		box-shadow: none;
	}
	.command-search :global([data-slot="input-group"]:focus-within) {
		border-color: var(--sqlviz-primary);
		box-shadow: var(--sqlviz-focus-ring);
	}
</style>
