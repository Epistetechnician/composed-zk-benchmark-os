import { useCallback, useEffect, useState } from 'react';

import type { CapabilityCatalog, LocalReplayStatus } from '../ipc/contract';

interface DesktopState {
  catalog: CapabilityCatalog | null;
  replay: LocalReplayStatus | null;
  error: string | null;
  refreshedAt: string | null;
}

const initialState: DesktopState = {
  catalog: null,
  replay: null,
  error: null,
  refreshedAt: null
};

function statusLabel(status: 'available' | 'unavailable' | 'planned'): string {
  return status === 'available' ? 'Available' : status === 'planned' ? 'Planned' : 'Unavailable';
}

export default function App() {
  const [state, setState] = useState<DesktopState>(initialState);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [catalog, replay] = await Promise.all([
        window.desktopApi.getCapabilityCatalog(),
        window.desktopApi.getLocalReplayStatus()
      ]);
      setState({
        catalog,
        replay,
        error: null,
        refreshedAt: new Date().toLocaleTimeString()
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : 'The desktop API could not be reached.'
      }));
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true">
          C
        </div>
        <div>
          <p className="eyebrow">Composed desktop</p>
          <p className="product-label">Electron Release 0</p>
        </div>
        <div className="topbar-spacer" />
        <span className="contract-pill">platform-ipc.v1</span>
        <button className="refresh-button" type="button" onClick={() => void refresh()} disabled={isRefreshing}>
          {isRefreshing ? 'Refreshing…' : 'Refresh state'}
        </button>
      </header>

      <section className="hero" aria-labelledby="page-title">
        <div>
          <p className="eyebrow accent">Local operator surface</p>
          <h1 id="page-title">Capability catalog</h1>
          <p className="hero-copy">
            A small, read-only shell for inspecting what this desktop build can expose locally.
            Execution remains deliberately outside this release.
          </p>
        </div>
        <div className="hero-note">
          <span className="note-dot" />
          <span>Local state only</span>
        </div>
      </section>

      {state.error ? <div className="error-banner" role="alert">{state.error}</div> : null}

      <div className="content-grid">
        <section className="panel catalog-panel" aria-labelledby="catalog-title">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Surface</p>
              <h2 id="catalog-title">Current capabilities</h2>
            </div>
            <span className="count-badge">{state.catalog?.capabilities.length ?? 0} entries</span>
          </div>

          <div className="capability-list">
            {state.catalog?.capabilities.map((capability) => (
              <article className="capability-row" key={capability.id}>
                <div className={`capability-icon ${capability.status}`} aria-hidden="true">
                  {capability.status === 'available' ? '✓' : capability.status === 'planned' ? '→' : '—'}
                </div>
                <div className="capability-copy">
                  <div className="capability-title-line">
                    <h3>{capability.label}</h3>
                    <span className={`status-tag ${capability.status}`}>{statusLabel(capability.status)}</span>
                  </div>
                  <p>{capability.description}</p>
                  <code>{capability.id}</code>
                </div>
              </article>
            )) ?? (
              <div className="empty-state">Loading the capability catalog…</div>
            )}
          </div>
        </section>

        <section className="panel replay-panel" aria-labelledby="replay-title">
          <div className="panel-heading">
            <div>
              <p className="section-kicker">Adapter state</p>
              <h2 id="replay-title">Local replay</h2>
            </div>
            <span className="status-tag unavailable">Unavailable</span>
          </div>

          <div className="replay-placeholder">
            <div className="replay-glyph" aria-hidden="true">↯</div>
            <h3>Replay is not connected</h3>
            <p>{state.replay?.message ?? 'Reading the local adapter state…'}</p>
            <div className="adapter-line">
              <span>Adapter seam</span>
              <code>{state.replay?.adapterId ?? 'rust-sidecar'}</code>
            </div>
          </div>

          <div className="boundary-list" aria-label="Release boundaries">
            <div><span>Native process execution</span><strong>Disabled</strong></div>
            <div><span>Arbitrary commands</span><strong>Not exposed</strong></div>
            <div><span>Renderer Node access</span><strong>Disabled</strong></div>
          </div>
        </section>
      </div>

      <footer className="footer-line">
        <span>Read-only Release 0 scaffold</span>
        <span>{state.refreshedAt ? `Last refreshed ${state.refreshedAt}` : 'Waiting for main process'}</span>
      </footer>
    </main>
  );
}
