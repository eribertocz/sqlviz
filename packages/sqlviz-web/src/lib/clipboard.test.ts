import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { copyText } from './clipboard';

/** jsdom implements neither `execCommand` nor a clipboard, so both are stubbed. */
function setSecureContext(secure: boolean) {
    Object.defineProperty(window, 'isSecureContext', { value: secure, configurable: true });
}

function stubClipboard(writeText: (t: string) => Promise<void>) {
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true });
}

/** Captures what the DOM looked like at the moment the copy fired. */
function stubExecCommand(onCopy?: () => void, result = true) {
    const spy = vi.fn(() => {
        onCopy?.();
        return result;
    });
    document.execCommand = spy as unknown as typeof document.execCommand;
    return spy;
}

function linkField(value: string): HTMLInputElement {
    const el = document.createElement('input');
    el.readOnly = true;
    el.value = value;
    document.body.appendChild(el);
    return el;
}

beforeEach(() => {
    document.body.innerHTML = '';
});

afterEach(() => {
    vi.restoreAllMocks();
    Reflect.deleteProperty(navigator, 'clipboard');
});

describe('copyText — secure context', () => {
    it('uses the Clipboard API and reports success', async () => {
        setSecureContext(true);
        const writeText = vi.fn().mockResolvedValue(undefined);
        stubClipboard(writeText);

        await expect(copyText('http://host/view/tok')).resolves.toBe(true);
        expect(writeText).toHaveBeenCalledWith('http://host/view/tok');
    });

    it('falls back to execCommand when the Clipboard API rejects', async () => {
        setSecureContext(true);
        stubClipboard(vi.fn().mockRejectedValue(new Error('denied')));
        const exec = stubExecCommand();

        await expect(copyText('secret')).resolves.toBe(true);
        expect(exec).toHaveBeenCalledWith('copy');
    });

    it('refuses to copy empty text', async () => {
        setSecureContext(true);
        const writeText = vi.fn().mockResolvedValue(undefined);
        stubClipboard(writeText);

        await expect(copyText('')).resolves.toBe(false);
        expect(writeText).not.toHaveBeenCalled();
    });
});

// Over http://<LAN-IP> there is no Clipboard API at all — this is the path
// every viewer machine actually takes.
describe('copyText — insecure context (LAN)', () => {
    beforeEach(() => setSecureContext(false));

    it('selects the source field in place instead of building a scratch one', async () => {
        const link = 'http://192.168.1.20:4000/view/abc';
        const el = linkField(link);
        const dialog = document.createElement('div');
        document.body.appendChild(dialog);

        let selection = '';
        let scratchCount = -1;
        stubExecCommand(() => {
            selection = el.value.slice(el.selectionStart ?? 0, el.selectionEnd ?? 0);
            scratchCount = dialog.querySelectorAll('textarea').length;
        });

        await expect(copyText(link, { source: el, container: dialog })).resolves.toBe(true);
        // The regression: the copy must carry the link, not a stray selection.
        expect(selection).toBe(link);
        expect(scratchCount).toBe(0);
    });

    it('restores the readonly attribute it had to lift to select', async () => {
        const link = 'http://192.168.1.20:4000/view/abc';
        const el = linkField(link);
        stubExecCommand(() => expect(el.hasAttribute('readonly')).toBe(false));

        await copyText(link, { source: el });
        expect(el.hasAttribute('readonly')).toBe(true);
    });

    it('puts the scratch field inside the container, then removes it', async () => {
        const dialog = document.createElement('div');
        document.body.appendChild(dialog);

        let scratch: HTMLTextAreaElement | null = null;
        stubExecCommand(() => {
            scratch = dialog.querySelector('textarea');
        });

        await expect(copyText('hunter2', { container: dialog })).resolves.toBe(true);
        // A body-level scratch field sits outside the dialog's focus trap, which
        // is what made the old implementation copy the wrong thing.
        expect(scratch).not.toBeNull();
        expect(scratch!.value).toBe('hunter2');
        expect(dialog.querySelector('textarea')).toBeNull();
        expect(document.body.querySelector('textarea')).toBeNull();
    });

    it('ignores a password field as source and uses the scratch field', async () => {
        const pw = document.createElement('input');
        pw.type = 'password';
        pw.value = 'hunter2';
        document.body.appendChild(pw);
        const dialog = document.createElement('div');
        document.body.appendChild(dialog);

        let scratchValue: string | undefined;
        stubExecCommand(() => {
            scratchValue = dialog.querySelector('textarea')?.value;
        });

        await copyText('hunter2', { source: pw, container: dialog });
        expect(scratchValue).toBe('hunter2');
    });

    it('ignores a stale source whose value no longer matches', async () => {
        const el = linkField('http://old-link');
        const dialog = document.createElement('div');
        document.body.appendChild(dialog);

        let scratchValue: string | undefined;
        stubExecCommand(() => {
            scratchValue = dialog.querySelector('textarea')?.value;
        });

        await copyText('http://new-link', { source: el, container: dialog });
        expect(scratchValue).toBe('http://new-link');
    });

    it('reports failure when execCommand refuses, leaving no scratch field behind', async () => {
        stubExecCommand(undefined, false);

        await expect(copyText('nope')).resolves.toBe(false);
        expect(document.body.querySelector('textarea')).toBeNull();
    });
});
