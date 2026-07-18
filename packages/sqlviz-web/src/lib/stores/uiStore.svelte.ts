const THEME_KEY  = 'sqlviz-theme';
const HEIGHT_KEY = 'sqlviz-editor-height';
const DEFAULT_EDITOR_HEIGHT_PX = 300;
const MIN_EDITOR_HEIGHT_PX = 120;
const MAX_EDITOR_HEIGHT_PX = 700;

function createUiStore() {
    let theme             = $state<'dark' | 'light'>('dark');
    let showScorePanel    = $state(false);
    let creatingDashboard = $state(false);
    let newDashboardName  = $state('');
    let toast             = $state<string | null>(null);
    let editorHeightPx    = $state(DEFAULT_EDITOR_HEIGHT_PX);

    let toastTimer = 0;

    /** Reads the persisted theme preference; call once on app mount. */
    function initTheme() {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved === 'light') {
            theme = 'light';
            document.documentElement.dataset.theme = 'light';
        }
        const savedHeight = Number(localStorage.getItem(HEIGHT_KEY));
        if (Number.isFinite(savedHeight) && savedHeight > 0) {
            editorHeightPx = clampHeight(savedHeight);
        }
    }

    function toggleTheme() {
        theme = theme === 'dark' ? 'light' : 'dark';
        if (theme === 'light') {
            document.documentElement.dataset.theme = 'light';
        } else {
            delete document.documentElement.dataset.theme;
        }
        localStorage.setItem(THEME_KEY, theme);
    }

    function clampHeight(px: number): number {
        return Math.min(MAX_EDITOR_HEIGHT_PX, Math.max(MIN_EDITOR_HEIGHT_PX, px));
    }

    function setEditorHeight(px: number) {
        editorHeightPx = clampHeight(px);
        localStorage.setItem(HEIGHT_KEY, String(editorHeightPx));
    }

    function showToast(msg: string, durationMs = 3500) {
        toast = msg;
        clearTimeout(toastTimer);
        toastTimer = window.setTimeout(() => { toast = null; }, durationMs);
    }

    return {
        get theme() { return theme; },
        get showScorePanel() { return showScorePanel; },
        set showScorePanel(v: boolean) { showScorePanel = v; },
        get creatingDashboard() { return creatingDashboard; },
        set creatingDashboard(v: boolean) { creatingDashboard = v; },
        get newDashboardName() { return newDashboardName; },
        set newDashboardName(v: string) { newDashboardName = v; },
        get toast() { return toast; },
        get editorHeightPx() { return editorHeightPx; },

        initTheme,
        toggleTheme,
        setEditorHeight,
        showToast,
    };
}

export const uiStore = createUiStore();
