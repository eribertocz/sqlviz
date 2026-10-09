/** Authorized read projection. Not Drawflow export and not a metadata repository. */
export interface MapNode {
    readonly id: string;
    readonly kind: 'query' | 'dataset' | 'visual' | 'panel' | 'dashboard' | 'text';
    readonly label: string;
    readonly x: number;
    readonly y: number;
}

export interface MapEdge {
    readonly sourceId: string;
    readonly targetId: string;
    readonly input: string;
}

export interface MapProjection {
    readonly nodes: readonly MapNode[];
    readonly edges: readonly MapEdge[];
}

function checkProjection(projection: MapProjection) {
    if (projection.nodes.length > 256 || projection.edges.length > 1024) {
        throw new Error('Map projection exceeds its budget');
    }
    const ids = new Set<string>();
    for (const node of projection.nodes) {
        if (typeof node.id !== 'string' || !node.id.trim() || ids.has(node.id)
            || !['query', 'dataset', 'visual', 'panel', 'dashboard', 'text'].includes(node.kind)
            || typeof node.label !== 'string' || node.label.length > 512
            || ![node.x, node.y].every(n => Number.isFinite(n) && n >= 0 && n <= 1_000_000)) {
            throw new Error('Invalid map node');
        }
        ids.add(node.id);
    }
    const edges = new Set<string>();
    for (const edge of projection.edges) {
        const key = JSON.stringify([edge.sourceId, edge.targetId, edge.input]);
        if (!ids.has(edge.sourceId) || !ids.has(edge.targetId)
            || typeof edge.input !== 'string' || !edge.input.trim() || edge.input.length > 256
            || edges.has(key)) throw new Error('Invalid map reference');
        edges.add(key);
    }
}

/** Mount only the read projection. Selection opens product context through a
 * callback; native connection editing/deletion cannot write SQLviz metadata.
 * A private subtree owns all Drawflow listeners and is removed on disposal.
 */
export async function mountDrawflowMap(
    host: HTMLElement, projection: MapProjection,
    options: { onSelect: (node: MapNode) => void; signal?: AbortSignal },
): Promise<{ destroy: () => void }> {
    if (typeof document === 'undefined') throw new Error('Drawflow requires a browser');
    checkProjection(projection);
    // Capture the generation before loading: caller mutations cannot change it.
    const nodes = projection.nodes.map(n => ({ ...n }));
    const edges = projection.edges.map(e => ({ ...e }));
    const { default: Drawflow } = await import('drawflow');
    await import('drawflow/dist/drawflow.min.css');
    if (options.signal?.aborted) throw new DOMException('Map mount cancelled', 'AbortError');
    const viewport = document.createElement('div');
    viewport.className = 'sqlviz-drawflow-map';
    // Drawflow positions its children absolutely; the private viewport must fill
    // the caller's measured area or a valid graph would render at zero height.
    viewport.style.width = '100%';
    viewport.style.height = '100%';
    host.append(viewport);
    const editor = new Drawflow(viewport);
    let disposed = false;
    const destroy = () => {
        if (disposed) return;
        disposed = true;
        options.signal?.removeEventListener('abort', destroy);
        editor.events = {};
        if (editor.precanvas) editor.clear();
        viewport.remove();
    };
    try {
        editor.editor_mode = 'fixed';
        editor.start();
        const nativeIds = new Map<string, number | string>();
        const ports = new Map<string, string[]>();
        for (const node of nodes) {
            ports.set(node.id, [...new Set(edges.filter(e => e.targetId === node.id).map(e => e.input))].sort());
        }
        for (const node of nodes) {
            // Only this constant HTML is interpreted. Labels use textContent.
            const id = editor.addNode(node.kind, ports.get(node.id)!.length,
                edges.some(e => e.sourceId === node.id) ? 1 : 0, node.x, node.y,
                `sqlviz-map-${node.kind}`, { objectId: node.id },
                '<button type="button" class="sqlviz-map-node-label"></button>', false);
            nativeIds.set(node.id, id);
            const button = viewport.querySelector<HTMLButtonElement>(`#node-${id} .sqlviz-map-node-label`)!;
            button.textContent = node.label;
            button.onclick = event => {
                event.stopPropagation();
                if (!disposed) options.onSelect({ ...node });
            };
            button.onmousedown = event => event.stopPropagation();
            button.ontouchstart = event => event.stopPropagation();
            button.onkeydown = event => event.stopPropagation();
        }
        for (const edge of edges) {
            const input = ports.get(edge.targetId)!.indexOf(edge.input) + 1;
            editor.addConnection(String(nativeIds.get(edge.sourceId)), String(nativeIds.get(edge.targetId)),
                'output_1', `input_${input}`);
        }
        options.signal?.addEventListener('abort', destroy, { once: true });
        return { destroy };
    } catch (error) {
        destroy();
        throw error;
    }
}
