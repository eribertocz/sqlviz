import type { GridStackEngine, GridStackMoveOpts, GridStackNode, GridStackOptions, GridStackWidget } from 'gridstack';
import type { GridStackEngineOptions } from 'gridstack/dist/gridstack-engine';

/** Internal S0 projection, not a new persisted layout or API contract. */
export interface CanvasPlacement {
    readonly panel_id: string;
    readonly column: number;
    readonly top_px: number;
    readonly column_span: number;
    readonly height_px: number;
}

const MAX_EXTENT = 1_000_000;

function checkGap(gapPx: number) {
    if (!Number.isSafeInteger(gapPx) || gapPx < 0 || gapPx > MAX_EXTENT) {
        throw new Error('Invalid canvas gap');
    }
}

function checkPlacements(placements: readonly CanvasPlacement[], gapPx: number) {
    checkGap(gapPx);
    if (placements.length > 256) throw new Error('Canvas projection exceeds its budget');
    const ids = new Set<string>();
    for (const p of placements) {
        if (typeof p.panel_id !== 'string' || !p.panel_id.trim() || ids.has(p.panel_id)) {
            throw new Error('Invalid or duplicate panel identity');
        }
        ids.add(p.panel_id);
        if (![p.column, p.column_span, p.top_px, p.height_px].every(Number.isSafeInteger)
            || p.column < 0 || p.column_span < 1 || p.column + p.column_span > 12
            || p.top_px < 0 || p.height_px < 120 || p.top_px + p.height_px > MAX_EXTENT) {
            throw new Error('Invalid panel geometry');
        }
    }
    for (let i = 0; i < placements.length; i++) {
        for (const b of placements.slice(i + 1)) {
            const a = placements[i];
            if (a.column < b.column + b.column_span && b.column < a.column + a.column_span
                && a.top_px < b.top_px + b.height_px + gapPx
                && b.top_px < a.top_px + a.height_px + gapPx) {
                throw new Error('Panel collision');
            }
        }
    }
}

/** One engine row = one CSS pixel. Reserve the trailing gap in each item's box.
 * The future DOM adapter must use a canvas width + gap and content inset by gap
 * on the right/bottom; it must not apply GridStack's default margins again.
 */
export function toGridStackWidgets(placements: readonly CanvasPlacement[], gapPx: number): GridStackWidget[] {
    checkPlacements(placements, gapPx);
    return placements.map(p => ({
        id: p.panel_id, x: p.column, y: p.top_px, w: p.column_span,
        h: p.height_px + gapPx, minW: 1, minH: 120 + gapPx,
        autoPosition: false, sizeToContent: false,
    }));
}

/** Ignore engine ordering and reject identity changes before accepting a draft. */
export function fromGridStackWidgets(
    widgets: readonly GridStackWidget[], previous: readonly CanvasPlacement[], gapPx: number,
): CanvasPlacement[] {
    checkPlacements(previous, gapPx);
    const byId = new Map(widgets.map(w => [w.id, w]));
    if (widgets.length !== previous.length || byId.size !== widgets.length) {
        throw new Error('Canvas identity set changed');
    }
    const result = previous.map(p => {
        const w = byId.get(p.panel_id);
        if (!w || w.x === undefined || w.y === undefined || w.w === undefined || w.h === undefined) {
            throw new Error('Missing panel identity or geometry');
        }
        return { panel_id: p.panel_id, column: w.x, top_px: w.y, column_span: w.w, height_px: w.h - gapPx };
    });
    checkPlacements(result, gapPx);
    return result;
}

export const CANVAS_GRIDSTACK_OPTIONS = {
    column: 12, cellHeight: 1, margin: 0, mode: 'float', animate: false,
    auto: false, acceptWidgets: false, removable: false, sizeToContent: false,
    handle: '.sqlviz-panel-drag-handle',
} as const satisfies GridStackOptions;

/** Browser-only loading keeps the dependency out of server module evaluation.
 * This preview engine rejects collisions rather than pushing/repacking neighbors.
 * The server still validates the full layout on commit.
 */
export async function loadCanvasEngineClass(gapPx = 16): Promise<typeof GridStackEngine> {
    checkGap(gapPx);
    if (typeof document === 'undefined') throw new Error('GridStack requires a browser');
    const { GridStackEngine: BaseEngine } = await import('gridstack');
    return class CanvasPreviewEngine extends BaseEngine {
        constructor(options: GridStackEngineOptions = {}) {
            super({ ...options, column: 12, mode: 'float' });
        }

        override moveNodeCheck(node: GridStackNode, options: GridStackMoveOpts): boolean {
            // The native implementation clamps first and may simulate neighbor pushes.
            return this.moveNode(node, options);
        }

        override moveNode(node: GridStackNode, options: GridStackMoveOpts): boolean {
            if (!node || !options || node.locked || !this.nodes.includes(node)) return false;
            const candidate = {
                x: options.x ?? node.x, y: options.y ?? node.y,
                w: options.w ?? node.w, h: options.h ?? node.h,
            };
            const { x, y, w, h } = candidate;
            if (x === undefined || y === undefined || w === undefined || h === undefined
                || ![x, y, w, h].every(Number.isSafeInteger)
                || x < 0 || y < 0 || w < Math.max(node.minW ?? 1, 1) || h < Math.max(node.minH ?? 1, 120 + gapPx)
                || x + w > 12 || y + h - gapPx > MAX_EXTENT
                || (node.maxW !== undefined && w > node.maxW)
                || (node.maxH !== undefined && h > node.maxH)
                || (this.maxRow > 0 && y + h > this.maxRow)
                || this.collide(node, candidate)) return false;
            // Prevent packing even if a caller asks for it; a separate explicit
            // product operation is needed to compact a confirmed dashboard.
            return super.moveNode(node, { ...options, ...candidate, pack: false });
        }
    };
}
