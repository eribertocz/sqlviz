import { describe, expect, it, vi } from 'vitest';
import { CANVAS_GRIDSTACK_OPTIONS, fromGridStackWidgets, loadCanvasEngineClass, toGridStackWidgets } from './gridstackCanvas';
import type { CanvasPlacement } from './gridstackCanvas';

function asymmetric(tallColumn = 0): CanvasPlacement[] {
    return [
        { panel_id: 'tall', column: tallColumn, top_px: 0, column_span: 6, height_px: 616 },
        { panel_id: 'upper', column: 6 - tallColumn, top_px: 0, column_span: 6, height_px: 300 },
        { panel_id: 'lower', column: 6 - tallColumn, top_px: 316, column_span: 6, height_px: 300 },
    ];
}

describe('GridStack canvas projection using the actual engine', () => {
    it.each([0, 6])('keeps a tall panel beside stacked neighbors at column %s', async column => {
        const source = asymmetric(column);
        const Engine = await loadCanvasEngineClass();
        const engine = new Engine();
        toGridStackWidgets(source, 16).forEach(w => engine.addNode({ ...w }));
        expect(fromGridStackWidgets(engine.nodes, source, 16)).toEqual(source);
        // Native engine sorting must not become SQL/panel document order.
        expect(fromGridStackWidgets([...engine.nodes].reverse(), source, 16)).toEqual(source);
    });

    it('preserves a one-pixel size change and intentional vertical whitespace', async () => {
        const source = asymmetric();
        const Engine = await loadCanvasEngineClass();
        const engine = new Engine();
        toGridStackWidgets(source, 16).forEach(w => engine.addNode({ ...w }));
        const upper = engine.nodes.find(n => n.id === 'upper')!;
        const lower = engine.nodes.find(n => n.id === 'lower')!;
        expect(engine.moveNode(upper, { h: 315 })).toBe(true); // content height = 299
        expect(engine.moveNode(lower, { y: 400 })).toBe(true);
        expect(fromGridStackWidgets(engine.nodes, source, 16)).toEqual([
            source[0], { ...source[1], height_px: 299 }, { ...source[2], top_px: 400 },
        ]);
        expect(source).toEqual(asymmetric());
    });

    it('rejects a drag or resize collision without pushing either neighbor', async () => {
        const source = asymmetric();
        const Engine = await loadCanvasEngineClass();
        const engine = new Engine();
        toGridStackWidgets(source, 16).forEach(w => engine.addNode({ ...w }));
        const upper = engine.nodes.find(n => n.id === 'upper')!;
        expect(engine.moveNodeCheck(upper, { h: 317 })).toBe(false);
        expect(engine.moveNodeCheck(upper, { x: 0 })).toBe(false);
        expect(fromGridStackWidgets(engine.nodes, source, 16)).toEqual(source);
    });

    it('rejects out-of-bounds and undersized proposals before native clamping', async () => {
        const source = asymmetric();
        const Engine = await loadCanvasEngineClass();
        const engine = new Engine();
        toGridStackWidgets(source, 16).forEach(w => engine.addNode({ ...w }));
        const tall = engine.nodes.find(n => n.id === 'tall')!;
        expect(engine.moveNodeCheck(tall, { x: -1 })).toBe(false);
        expect(engine.moveNodeCheck(tall, { h: 18 })).toBe(false); // content height = 2
        expect(engine.moveNodeCheck(tall, { x: 7 })).toBe(false);
        expect(fromGridStackWidgets(engine.nodes, source, 16)).toEqual(source);
        expect(CANVAS_GRIDSTACK_OPTIONS.cellHeight).toBe(1);
    });

    it('does not pack neighbors after moving a panel even when packing was requested', async () => {
        const source = asymmetric();
        const Engine = await loadCanvasEngineClass();
        const engine = new Engine();
        toGridStackWidgets(source, 16).forEach(w => engine.addNode({ ...w }));
        expect(engine.moveNode(engine.nodes.find(n => n.id === 'tall')!, { y: 700, pack: true })).toBe(true);
        expect(fromGridStackWidgets(engine.nodes, source, 16)).toEqual([
            { ...source[0], top_px: 700 }, source[1], source[2],
        ]);
    });

    it('rejects missing, unknown and duplicated identities returned by the engine', () => {
        const source = asymmetric();
        const widgets = toGridStackWidgets(source, 16);
        expect(() => fromGridStackWidgets(widgets.slice(1), source, 16)).toThrow();
        expect(() => fromGridStackWidgets([{ ...widgets[0], id: 'unknown' }, ...widgets.slice(1)], source, 16)).toThrow();
        expect(() => fromGridStackWidgets([widgets[0], widgets[0], widgets[2]], source, 16)).toThrow();
    });

    it('accounts for the trailing engine gap separately near the canvas extent budget', async () => {
        const source = [{ panel_id: 'last', column: 0, top_px: 999848, column_span: 12, height_px: 120 }];
        const Engine = await loadCanvasEngineClass(80);
        const engine = new Engine();
        toGridStackWidgets(source, 80).forEach(w => engine.addNode({ ...w }));
        expect(engine.moveNodeCheck(engine.nodes[0], { y: 999847 })).toBe(true);
        expect(fromGridStackWidgets(engine.nodes, source, 80)[0].top_px).toBe(999847);
    });

    it('rejects server-side engine creation before evaluating the browser dependency', async () => {
        vi.stubGlobal('document', undefined);
        try {
            await expect(loadCanvasEngineClass()).rejects.toThrow('requires a browser');
        } finally {
            vi.unstubAllGlobals();
        }
    });
});
