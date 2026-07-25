/**
 * Copying text to the clipboard, including from inside a focus-trapped dialog.
 *
 * Two failure modes drive the shape of this module:
 *
 * 1. `navigator.clipboard` only exists in a secure context. SQLviz dashboards
 *    are shared over `http://<LAN-IP>`, so on every machine except the host it
 *    is unavailable and we must fall back to `document.execCommand('copy')`.
 *
 * 2. `execCommand('copy')` copies the *current selection*. The usual trick —
 *    append an off-screen <textarea> to <body>, focus it, select it — silently
 *    copies the wrong thing inside a bits-ui dialog: the dialog traps focus, so
 *    it yanks focus back from any element outside its content before the copy
 *    runs, leaving whatever the user had selected before as the payload.
 *    Anything we select must therefore live *inside* the dialog element.
 */

export type CopyOptions = {
    /**
     * A field already holding exactly `text` (e.g. the visible link input).
     * Selected in place, which is both cheaper and immune to problem 2 above.
     */
    source?: HTMLInputElement | HTMLTextAreaElement | null;
    /**
     * Where the scratch <textarea> is appended when there is no usable
     * `source`. Pass the dialog content node when copying from inside a
     * dialog, otherwise focus never lands on it. Defaults to <body>.
     */
    container?: HTMLElement | null;
};

/** Copies `text`, returning whether it actually reached the clipboard. */
export async function copyText(text: string, opts: CopyOptions = {}): Promise<boolean> {
    if (!text) return false;
    try {
        if (window.isSecureContext && navigator.clipboard) {
            await navigator.clipboard.writeText(text);
            return true;
        }
    } catch {
        // Blocked by permissions or a hostile embedder — try the legacy path.
    }
    return execCommandCopy(text, opts);
}

function execCommandCopy(text: string, { source, container }: CopyOptions): boolean {
    const target = usableSource(source, text) ?? scratchField(text, container ?? document.body);
    const scratch = target !== source;
    const wasReadonly = target.hasAttribute('readonly');
    const previous = document.activeElement as HTMLElement | null;
    try {
        // iOS Safari refuses to select the contents of a readonly field.
        target.removeAttribute('readonly');
        target.focus({ preventScroll: true });
        target.setSelectionRange(0, target.value.length);
        return document.execCommand('copy');
    } catch {
        return false;
    } finally {
        if (wasReadonly) target.setAttribute('readonly', '');
        if (scratch) target.remove();
        // Put the caret back on the button the user pressed.
        previous?.focus?.({ preventScroll: true });
    }
}

/**
 * A source field is only usable when it still holds exactly what we were asked
 * to copy — and never for a password field, whose selection browsers refuse to
 * expose. Falling back to the scratch field keeps those cases correct.
 */
function usableSource(
    source: CopyOptions['source'],
    text: string,
): HTMLInputElement | HTMLTextAreaElement | null {
    if (!source || source.value !== text) return null;
    if (source instanceof HTMLInputElement && source.type === 'password') return null;
    return source;
}

function scratchField(text: string, root: HTMLElement): HTMLTextAreaElement {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('aria-hidden', 'true');
    ta.tabIndex = -1;
    // Off-screen, but never `display:none` / `visibility:hidden` — a field that
    // isn't rendered can't hold a selection, which makes the copy a no-op.
    ta.style.cssText =
        'position:fixed;top:0;left:0;width:1px;height:1px;padding:0;border:0;opacity:0;pointer-events:none;';
    root.appendChild(ta);
    return ta;
}
