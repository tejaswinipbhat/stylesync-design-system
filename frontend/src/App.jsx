import { useState, useCallback } from "react";
import Preview from "./Preview";

const API = "http://localhost:8000";

// ─── Helpers ──────────────────────────────────────────────────────────────────

function hexToRgb(hex) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

// ─── Skeleton Loader ──────────────────────────────────────────────────────────

function SkeletonSidebar() {
  return (
    <div className="sidebar-content">
      <div className="token-group">
        <div className="token-group-label">
          <div className="skeleton skeleton-line" style={{ width: "60px" }} />
        </div>
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="color-token" style={{ gap: 10 }}>
            <div className="skeleton skeleton-swatch" />
            <div style={{ flex: 1 }}>
              <div className="skeleton skeleton-line" style={{ width: "70%", marginBottom: 4 }} />
              <div className="skeleton skeleton-line" style={{ width: "50%" }} />
            </div>
          </div>
        ))}
      </div>
      <div className="token-group">
        <div className="token-group-label">
          <div className="skeleton skeleton-line" style={{ width: "80px" }} />
        </div>
        {[1, 2].map((i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <div className="skeleton skeleton-line" style={{ width: "40%", marginBottom: 6 }} />
            <div className="skeleton" style={{ height: 30, borderRadius: 6 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function SkeletonPreview() {
  return (
    <div className="preview-grid fade-in">
      {[1, 2, 3].map((i) => (
        <div key={i} className="preview-section">
          <div className="preview-section-header">
            <div className="skeleton skeleton-line" style={{ width: "100px" }} />
          </div>
          <div className="preview-section-body">
            <div className="skeleton skeleton-block" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Color Token ──────────────────────────────────────────────────────────────

function ColorToken({ name, value, locked, onUpdate, onToggleLock }) {
  return (
    <div className={`color-token ${locked ? "locked" : ""}`}>
      <div
        className="color-swatch"
        style={{ background: value }}
        title={`Click to edit ${name}`}
      >
        <input
          type="color"
          className="color-swatch-input"
          value={value.startsWith("#") ? value : "#000000"}
          disabled={locked}
          onChange={(e) => onUpdate(name, e.target.value)}
        />
      </div>
      <div className="color-token-info">
        <div className="color-token-name">{name}</div>
        <div className="color-token-value">{value}</div>
      </div>
      <button
        className={`lock-btn ${locked ? "locked" : ""}`}
        onClick={() => onToggleLock("colors", name, value)}
        title={locked ? "Unlock token" : "Lock token"}
      >
        {locked ? "🔒" : "🔓"}
      </button>
    </div>
  );
}

// ─── Spacing Visualizer ───────────────────────────────────────────────────────

function SpacingVisualizer({ spacing, onChange }) {
  const named = spacing?.named || {};
  const maxVal = 64;

  return (
    <div>
      {Object.entries(named).map(([key, val]) => {
        const px = parseInt(val) || 0;
        const pct = Math.min((px / maxVal) * 100, 100);

        const handleMouseDown = (e) => {
          const wrap = e.currentTarget;
          const rect = wrap.getBoundingClientRect();

          const move = (ev) => {
            const ratio = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
            const newPx = Math.round(ratio * maxVal / 4) * 4;
            onChange(key, `${newPx}px`);
          };

          const up = () => {
            document.removeEventListener("mousemove", move);
            document.removeEventListener("mouseup", up);
          };

          document.addEventListener("mousemove", move);
          document.addEventListener("mouseup", up);
          move(e);
        };

        return (
          <div key={key} className="spacing-token">
            <span className="spacing-label">{key}</span>
            <div className="spacing-bar-wrap" onMouseDown={handleMouseDown}>
              <div className="spacing-bar" style={{ width: `${pct}%` }} />
            </div>
            <span className="spacing-value">{val}</span>
          </div>
        );
      })}
    </div>
  );
}

// ─── Typography Editor ────────────────────────────────────────────────────────

function TypographyEditor({ typography, onChange }) {
  const fields = [
    { key: "headingFont", label: "Heading Font" },
    { key: "bodyFont", label: "Body Font" },
    { key: "monoFont", label: "Mono Font" },
    { key: "baseSize", label: "Base Size" },
  ];

  return (
    <div>
      {fields.map(({ key, label }) => (
        <div key={key} className="typo-token">
          <div className="typo-token-label">{label}</div>
          <input
            className="typo-token-input"
            value={typography?.[key] || ""}
            onChange={(e) => onChange(key, e.target.value)}
          />
        </div>
      ))}
      <div className="typo-preview" style={{
        fontFamily: typography?.bodyFont || "inherit",
        fontSize: typography?.baseSize || "14px",
      }}>
        The quick brown fox jumps over the lazy dog.
      </div>
    </div>
  );
}

// ─── Export Panel ─────────────────────────────────────────────────────────────

function ExportPanel({ siteId, tokens }) {
  const [copied, setCopied] = useState(null);

  const copyText = (text, label) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(label);
      setTimeout(() => setCopied(null), 2000);
    });
  };

  const generateCSS = () => {
    const c = tokens?.colors || {};
    const t = tokens?.typography || {};
    const s = tokens?.spacing?.named || {};
    const r = tokens?.borderRadius || {};
    const sh = tokens?.shadows || {};

    const lines = [":root {"];
    Object.entries(c).forEach(([k, v]) => lines.push(`  --color-${k}: ${v};`));
    if (t.headingFont) lines.push(`  --font-heading: ${t.headingFont};`);
    if (t.bodyFont) lines.push(`  --font-body: ${t.bodyFont};`);
    if (t.baseSize) lines.push(`  --font-size-base: ${t.baseSize};`);
    Object.entries(s).forEach(([k, v]) => lines.push(`  --spacing-${k}: ${v};`));
    Object.entries(r).forEach(([k, v]) => lines.push(`  --radius-${k}: ${v};`));
    Object.entries(sh).forEach(([k, v]) => lines.push(`  --shadow-${k}: ${v};`));
    lines.push("}");
    return lines.join("\n");
  };

  const generateJSON = () =>
    JSON.stringify(tokens || {}, null, 2);

  const generateTailwind = () => {
    const c = tokens?.colors || {};
    const r = tokens?.borderRadius || {};
    const s = tokens?.spacing?.named || {};
    return `/** @type {import('tailwindcss').Config} */
module.exports = {
  theme: {
    extend: {
      colors: ${JSON.stringify(c, null, 8)},
      spacing: ${JSON.stringify(s, null, 8)},
      borderRadius: ${JSON.stringify(r, null, 8)},
      fontFamily: {
        heading: ["${tokens?.typography?.headingFont || 'Inter'}"],
        body: ["${tokens?.typography?.bodyFont || 'Inter'}"],
      },
    },
  },
};`;
  };

  const actions = [
    { label: "CSS Vars", icon: "📋", fn: () => copyText(generateCSS(), "CSS Vars") },
    { label: "JSON", icon: "{ }", fn: () => copyText(generateJSON(), "JSON") },
    { label: "Tailwind", icon: "🌊", fn: () => copyText(generateTailwind(), "Tailwind") },
  ];

  return (
    <div className="export-panel">
      {actions.map(({ label, icon, fn }) => (
        <button
          key={label}
          className={`btn-export ${copied === label ? "copied" : ""}`}
          onClick={fn}
          title={`Copy ${label}`}
        >
          <span>{icon}</span>
          <span>{copied === label ? "Copied!" : label}</span>
        </button>
      ))}
    </div>
  );
}

// ─── Version History ──────────────────────────────────────────────────────────

function VersionHistory({ history }) {
  if (!history?.length) {
    return (
      <div style={{ padding: "20px 0", textAlign: "center", color: "var(--text-muted)", fontSize: 12 }}>
        No changes recorded yet.
      </div>
    );
  }

  return (
    <div>
      {history.map((item) => (
        <div key={item.id} className="history-item">
          <div className={`history-dot ${item.change_type}`} />
          <div className="history-info">
            <div className="history-desc">
              {item.change_type === "lock" && `🔒 Locked `}
              {item.change_type === "unlock" && `🔓 Unlocked `}
              {item.change_type === "edit" && `✏️ Updated `}
              <strong>{item.token_key}</strong>
              {item.token_category && ` in ${item.token_category}`}
              {item.after_value && item.change_type === "edit" &&
                ` → ${item.after_value?.replace(/"/g, "")}`}
            </div>
            <div className="history-time">{timeAgo(item.created_at)}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [siteInfo, setSiteInfo] = useState(null);
  const [siteId, setSiteId] = useState(null);
  const [tokens, setTokens] = useState(null);
  const [locked, setLocked] = useState({});   // { category: { key: true } }
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("colors");

  // ── Scrape ──────────────────────────────────────────────────────────────────

  const handleScrape = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setError(null);
    setSiteInfo(null);
    setTokens(null);
    setLocked({});
    setHistory([]);
    setSiteId(null);

    try {
      const res = await fetch(`${API}/api/scrape`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });

      const data = await res.json();

      if (!data.success) {
        setError({ message: "Unable to analyze this website", suggestion: data.suggestion });
        return;
      }

      setSiteInfo({ title: data.title, favicon_url: data.favicon_url, url: data.url });
      setSiteId(data.site_id);
      setTokens(data.tokens);
    } catch (err) {
      setError({
        message: "Connection error",
        suggestion: "Make sure the StyleSync backend is running on port 8000.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleScrape();
  };

  // ── Token Update ─────────────────────────────────────────────────────────────

  const updateToken = useCallback((category, key, value) => {
    setTokens((prev) => ({
      ...prev,
      [category]: { ...prev?.[category], [key]: value },
    }));

    // Record in history locally
    setHistory((prev) => [
      {
        id: Date.now(),
        change_type: "edit",
        token_category: category,
        token_key: key,
        after_value: JSON.stringify(value),
        created_at: new Date().toISOString(),
      },
      ...prev.slice(0, 49),
    ]);

    // Persist to DB if we have a siteId
    if (siteId && siteId > 0) {
      fetch(`${API}/api/tokens/${siteId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category, key, value }),
      }).catch(() => {});
    }
  }, [siteId]);

  // ── Lock Toggle ────────────────────────────────────────────────────────────

  const toggleLock = useCallback((category, key, value) => {
    const isLocked = locked?.[category]?.[key];

    setLocked((prev) => ({
      ...prev,
      [category]: {
        ...prev?.[category],
        [key]: !isLocked,
      },
    }));

    setHistory((prev) => [
      {
        id: Date.now(),
        change_type: isLocked ? "unlock" : "lock",
        token_category: category,
        token_key: key,
        created_at: new Date().toISOString(),
      },
      ...prev.slice(0, 49),
    ]);

    if (siteId && siteId > 0) {
      if (!isLocked) {
        fetch(`${API}/api/tokens/${siteId}/lock`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ category, key, value: String(value) }),
        }).catch(() => {});
      } else {
        fetch(`${API}/api/tokens/${siteId}/lock/${category}/${key}`, {
          method: "DELETE",
        }).catch(() => {});
      }
    }
  }, [locked, siteId]);

  // ── Sidebar Tabs ───────────────────────────────────────────────────────────

  const tabs = [
    { id: "colors", label: "Colors" },
    { id: "typography", label: "Type" },
    { id: "spacing", label: "Space" },
    { id: "history", label: "History" },
  ];

  const renderSidebarContent = () => {
    if (loading) return <SkeletonSidebar />;

    if (!tokens) {
      return (
        <div style={{ padding: "24px 8px", color: "var(--text-muted)", fontSize: 12, lineHeight: 1.6 }}>
          Paste a URL above and click Analyze to extract design tokens from any website.
        </div>
      );
    }

    if (activeTab === "colors") {
      return (
        <div className="sidebar-content">
          {error && (
            <div className="error-banner">
              <span className="error-banner-icon">⚠️</span>
              <div>
                <div className="error-banner-title">{error.message}</div>
                <div className="error-banner-desc">{error.suggestion}</div>
              </div>
            </div>
          )}
          <div className="token-group">
            <div className="token-group-label">
              Color Palette
              <span className="badge badge-extracted">Extracted</span>
            </div>
            {Object.entries(tokens.colors || {}).map(([name, value]) => (
              <ColorToken
                key={name}
                name={name}
                value={value}
                locked={!!locked?.colors?.[name]}
                onUpdate={(k, v) => updateToken("colors", k, v)}
                onToggleLock={toggleLock}
              />
            ))}
          </div>

          {Object.keys(tokens.borderRadius || {}).length > 0 && (
            <div className="token-group">
              <div className="token-group-label">Border Radius</div>
              {Object.entries(tokens.borderRadius || {}).map(([name, value]) => (
                <div key={name} className="color-token">
                  <div style={{
                    width: 30, height: 30, border: "2px solid var(--accent)",
                    borderRadius: value, background: "transparent", flexShrink: 0
                  }} />
                  <div className="color-token-info">
                    <div className="color-token-name">{name}</div>
                    <div className="color-token-value">{value}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (activeTab === "typography") {
      return (
        <div className="sidebar-content">
          <div className="token-group">
            <div className="token-group-label">Typography</div>
            <TypographyEditor
              typography={tokens.typography}
              onChange={(key, val) => updateToken("typography", key, val)}
            />
          </div>

          {tokens.typography?.scale && (
            <div className="token-group">
              <div className="token-group-label">Type Scale</div>
              {Object.entries(tokens.typography.scale).map(([tag, props]) => (
                <div key={tag} className="typo-token">
                  <div className="typo-token-label">{tag.toUpperCase()} — {props.size}</div>
                  <div style={{
                    fontFamily: tokens.typography?.bodyFont || "inherit",
                    fontSize: "12px",
                    color: "var(--text-secondary)",
                    fontWeight: props.weight,
                  }}>
                    Sample heading text
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (activeTab === "spacing") {
      return (
        <div className="sidebar-content">
          <div className="token-group">
            <div className="token-group-label">Spacing Scale</div>
            <SpacingVisualizer
              spacing={tokens.spacing}
              onChange={(key, val) => {
                updateToken("spacing", "named", { ...tokens.spacing?.named, [key]: val });
              }}
            />
          </div>

          {tokens.shadows && (
            <div className="token-group">
              <div className="token-group-label">Shadows</div>
              {Object.entries(tokens.shadows).map(([name, value]) => (
                <div key={name} className="color-token">
                  <div style={{
                    width: 30, height: 30, borderRadius: 6,
                    background: "var(--surface)",
                    boxShadow: value, flexShrink: 0
                  }} />
                  <div className="color-token-info">
                    <div className="color-token-name">{name}</div>
                    <div className="color-token-value" style={{ fontSize: 9 }}>{value}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    if (activeTab === "history") {
      return (
        <div className="sidebar-content">
          <div className="token-group">
            <div className="token-group-label">Change History</div>
            <VersionHistory history={history} />
          </div>
        </div>
      );
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="app-layout">
      <header className="app-header">
        <div className="app-header-logo">
          <div className="logo-mark">✦</div>
          StyleSync
        </div>

        <div className="url-bar">
          <span className="url-bar-icon">🌐</span>
          <input
            className="url-input"
            type="url"
            placeholder="https://example.com — paste any URL to analyze"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        </div>

        <button
          className="btn-analyze"
          onClick={handleScrape}
          disabled={loading || !url.trim()}
        >
          {loading ? (
            <>
              <span className="pulse">●</span> Analyzing…
            </>
          ) : (
            <>✦ Analyze</>
          )}
        </button>

        {tokens && (
          <div className="header-actions">
            <ExportPanel siteId={siteId} tokens={tokens} />
          </div>
        )}
      </header>

      {/* Site info bar */}
      {siteInfo && (
        <div className="site-info-bar">
          {siteInfo.favicon_url && (
            <img className="site-favicon" src={siteInfo.favicon_url} alt="" />
          )}
          <span className="site-title">{siteInfo.title || siteInfo.url}</span>
          <span>·</span>
          <span className="site-url">{siteInfo.url}</span>
          <span style={{ marginLeft: "auto" }}>
            <span className="badge badge-extracted">
              ✓ {Object.keys(tokens?.colors || {}).length} colors extracted
            </span>
          </span>
        </div>
      )}

      <div className="app-body">
        <aside className="sidebar">
          <div className="sidebar-tabs">
            {tabs.map((tab) => (
              <div
                key={tab.id}
                className={`sidebar-tab ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
                {tab.id === "history" && history.length > 0 && (
                  <span style={{
                    marginLeft: 4,
                    background: "var(--accent-dim)",
                    color: "var(--accent)",
                    borderRadius: 10,
                    padding: "0 5px",
                    fontSize: 9,
                    fontWeight: 700,
                  }}>
                    {history.length}
                  </span>
                )}
              </div>
            ))}
          </div>
          {renderSidebarContent()}
        </aside>

        <main className="preview-panel">
          {error && !tokens && (
            <div className="error-banner fade-in" style={{ maxWidth: 500 }}>
              <span className="error-banner-icon">⚠️</span>
              <div>
                <div className="error-banner-title">{error.message}</div>
                <div className="error-banner-desc">{error.suggestion}</div>
              </div>
            </div>
          )}

          {loading && <SkeletonPreview />}

          {!loading && !tokens && !error && (
            <div className="empty-state">
              <div className="empty-state-icon">✦</div>
              <div className="empty-state-title">Your design system awaits</div>
              <div className="empty-state-desc">
                Paste any website URL above to instantly extract its colors,
                typography, and spacing into an interactive design token editor.
              </div>
            </div>
          )}

          {tokens && !loading && (
            <div className="fade-in">
              <div className="preview-header">
                <span className="preview-title">Live Preview</span>
              </div>
              <Preview tokens={tokens} locked={locked} />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
