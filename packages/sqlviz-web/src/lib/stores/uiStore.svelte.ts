const THEME_KEY  = 'sqlviz-theme';
const HEIGHT_KEY = 'sqlviz-editor-height';
const SIDEBAR_KEY = 'sqlviz-sidebar-collapsed';
const DEFAULT_EDITOR_HEIGHT_PX = 300;
const MIN_EDITOR_HEIGHT_PX = 120;
const MAX_EDITOR_HEIGHT_PX = 700;

function readPreference(key: string): string | null {
    try { return localStorage.getItem(key); }
    catch { return null; }
}

function writePreference(key: string, value: string) {
    try { localStorage.setItem(key, value); }
    catch { /* Preferences must not block navigation when storage is unavailable. */ }
}

function createUiStore() {
    let theme             = $state<'dark' | 'light'>('dark');
    let showScorePanel    = $state(false);
    let creatingDashboard = $state(false);
    let newDashboardName  = $state('');
    let toast             = $state<string | null>(null);
    let editorHeightPx    = $state(DEFAULT_EDITOR_HEIGHT_PX);
    // Hidden by default: the dashboard uses the entire width. The header
    // always exposes navigation; opening it never depends on hover.
    let sidebarCollapsed  = $state(true);
    // Focus / Zen mode — hides all chrome for a full-bleed dashboard.
    let focusMode         = $state(false);
    // Editor drawer visibility (floats over the dashboard rather than pushing).
    let editorOpen        = $state(true);

    let toastTimer = 0;

    /** Reads the persisted theme preference; call once on app mount. */
    function initTheme() {
        const saved = readPreference(THEME_KEY);
        if (saved === 'light') {
            theme = 'light';
            document.documentElement.dataset.theme = 'light';
        }
        const savedHeight = Number(readPreference(HEIGHT_KEY));
        if (Number.isFinite(savedHeight) && savedHeight > 0) {
            editorHeightPx = clampHeight(savedHeight);
        }
        const savedSidebar = readPreference(SIDEBAR_KEY);
        if (savedSidebar === '0') sidebarCollapsed = false;
        else if (savedSidebar === '1') sidebarCollapsed = true;
    }

    function setSidebarCollapsed(value: boolean) {
        sidebarCollapsed = value;
        writePreference(SIDEBAR_KEY, sidebarCollapsed ? '1' : '0');
    }

    function toggleSidebar() { setSidebarCollapsed(!sidebarCollapsed); }

    function toggleTheme() {
        theme = theme === 'dark' ? 'light' : 'dark';
        if (theme === 'light') {
            document.documentElement.dataset.theme = 'light';
        } else {
            delete document.documentElement.dataset.theme;
        }
        writePreference(THEME_KEY, theme);
    }

    function toggleFocusMode() { focusMode = !focusMode; }
    function toggleEditor()    { editorOpen = !editorOpen; }

    function clampHeight(px: number): number {
        return Math.min(MAX_EDITOR_HEIGHT_PX, Math.max(MIN_EDITOR_HEIGHT_PX, px));
    }

    function setEditorHeight(px: number) {
        editorHeightPx = clampHeight(px);
        writePreference(HEIGHT_KEY, String(editorHeightPx));
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
        get sidebarCollapsed() { return sidebarCollapsed; },
        get focusMode() { return focusMode; },
        set focusMode(v: boolean) { focusMode = v; },
        get editorOpen() { return editorOpen; },
        set editorOpen(v: boolean) { editorOpen = v; },

        initTheme,
        toggleTheme,
        toggleSidebar,
        setSidebarCollapsed,
        toggleFocusMode,
        toggleEditor,
        setEditorHeight,
        showToast,
    };
}

export const uiStore = createUiStore();
