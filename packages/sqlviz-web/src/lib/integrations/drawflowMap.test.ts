import { afterEach, expect, it, vi } from 'vitest';
import { mountDrawflowMap } from './drawflowMap';
import type { MapProjection } from './drawflowMap';

afterEach(() => document.body.replaceChildren());

function projection(): MapProjection {
    return {
        nodes: [
            { id: 'sales', kind: 'dataset', label: 'Sales', x: 0, y: 0 },
            { id: 'costs', kind: 'dataset', label: 'Costs', x: 0, y: 180 },
            { id: 'trend', kind: 'visual', label: 'Trend', x: 300, y: 0 },
            { id: 'bars', kind: 'visual', label: 'Bars', x: 300, y: 180 },
        ],
        edges: [
            { sourceId: 'sales', targetId: 'trend', input: 'primary' },
            { sourceId: 'costs', targetId: 'trend', input: 'comparison' },
            { sourceId: 'sales', targetId: 'bars', input: 'primary' },
        ],
    };
}

function host() {
    const host = document.createElement('div');
    document.body.append(host);
    return host;
}

it('renders reused datasets once and keeps distinct named inputs using real Drawflow', async () => {
    const container = host();
    const onSelect = vi.fn();
    const session = await mountDrawflowMap(container, projection(), { onSelect });
    expect(container.querySelectorAll('.drawflow-node')).toHaveLength(4);
    expect(container.querySelectorAll('.connection')).toHaveLength(3);
    expect(container.querySelectorAll('.sqlviz-map-visual .inputs .input')).toHaveLength(3);
    const trend = [...container.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === 'Trend')!;
    trend.click();
    expect(onSelect).toHaveBeenCalledWith(projection().nodes[2]);
    session.destroy();
});

it('renders markup-like labels as text, never as library HTML', async () => {
    const container = host();
    const source = projection();
    const session = await mountDrawflowMap(container, {
        ...source, nodes: [{ ...source.nodes[0], label: '<img src=x onerror="alert(1)">' }, ...source.nodes.slice(1)],
    }, { onSelect: vi.fn() });
    expect(container.querySelector('img')).toBeNull();
    expect(container.textContent).toContain('<img src=x onerror="alert(1)">');
    session.destroy();
});

it('does not let native Delete/context menu remove dependency nodes', async () => {
    const container = host();
    const session = await mountDrawflowMap(container, projection(), { onSelect: vi.fn() });
    const node = container.querySelector<HTMLElement>('.drawflow-node')!;
    node.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, button: 0 }));
    node.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Delete' }));
    node.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true }));
    expect(container.querySelectorAll('.drawflow-node')).toHaveLength(4);
    expect(container.querySelectorAll('.connection')).toHaveLength(3);
    session.destroy();
});

it('rejects dangling references and duplicate objects before touching the host', async () => {
    const container = host();
    container.textContent = 'Preserve existing content';
    const source = projection();
    await expect(mountDrawflowMap(container, {
        ...source, edges: [{ sourceId: 'unknown', targetId: 'trend', input: 'primary' }],
    }, { onSelect: vi.fn() })).rejects.toThrow('Invalid map reference');
    await expect(mountDrawflowMap(container, {
        ...source, nodes: [...source.nodes, source.nodes[0]],
    }, { onSelect: vi.fn() })).rejects.toThrow('Invalid map node');
    expect(container.textContent).toBe('Preserve existing content');
});

it('disposes its private subtree on abort without clearing caller-owned content', async () => {
    const container = host();
    const sentinel = document.createElement('p');
    sentinel.textContent = 'Caller content';
    container.append(sentinel);
    const controller = new AbortController();
    const onSelect = vi.fn();
    const session = await mountDrawflowMap(container, projection(), { onSelect, signal: controller.signal });
    const oldButton = container.querySelector<HTMLButtonElement>('button')!;
    controller.abort();
    session.destroy();
    oldButton.click();
    expect(onSelect).not.toHaveBeenCalled();
    expect([...container.children]).toEqual([sentinel]);
    const reopened = await mountDrawflowMap(container, projection(), { onSelect });
    container.querySelector<HTMLButtonElement>('button')!.click();
    expect(onSelect).toHaveBeenCalledTimes(1);
    reopened.destroy();
});

it('does not mount a generation already abandoned while loading', async () => {
    const container = host();
    const controller = new AbortController();
    const pending = mountDrawflowMap(container, projection(), { onSelect: vi.fn(), signal: controller.signal });
    controller.abort();
    await expect(pending).rejects.toMatchObject({ name: 'AbortError' });
    expect(container.children).toHaveLength(0);
});

it('rejects server-side mounting before evaluating the browser dependency', async () => {
    const container = host();
    vi.stubGlobal('document', undefined);
    try {
        await expect(mountDrawflowMap(container, projection(), { onSelect: vi.fn() })).rejects.toThrow('requires a browser');
    } finally {
        vi.unstubAllGlobals();
    }
});
