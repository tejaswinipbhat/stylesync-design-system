// Preview.jsx — Live component grid that consumes CSS custom properties

export default function Preview({ tokens, locked }) {
  const colors = tokens?.colors || {};
  const typo = tokens?.typography || {};
  const spacing = tokens?.spacing || {};
  const borderRadius = tokens?.borderRadius || {};
  const shadows = tokens?.shadows || {};

  // Map extracted tokens → CSS custom properties for the preview
  const cssVars = {
    "--preview-color-primary":    colors.primary    || "#7c6ef5",
    "--preview-color-secondary":  colors.secondary  || "#334155",
    "--preview-color-accent":     colors.accent     || "#7c6ef5",
    "--preview-color-background": colors.background || "#ffffff",
    "--preview-color-surface":    colors.surface    || "#1c1c26",
    "--preview-color-text":       colors.text       || "#f0f0f5",
    "--preview-color-text-muted": colors.textMuted  || "#64748b",
    "--preview-color-border":     colors.border     || "rgba(255,255,255,0.08)",
    "--preview-font-heading":     typo.headingFont  || "Inter, system-ui, sans-serif",
    "--preview-font-body":        typo.bodyFont     || "Inter, system-ui, sans-serif",
    "--preview-radius-sm":        borderRadius.sm   || "4px",
    "--preview-radius-md":        borderRadius.md   || "8px",
    "--preview-radius-lg":        borderRadius.lg   || "12px",
    "--preview-radius-full":      borderRadius.full || "9999px",
    "--preview-shadow-md":        shadows.md        || "0 4px 16px rgba(0,0,0,0.2)",
    "--preview-shadow-lg":        shadows.lg        || "0 10px 30px rgba(0,0,0,0.2)",
  };

  const scale = typo?.scale || {};

  return (
    <div style={cssVars} className="preview-grid">

      {/* ── Color Palette ──────────────────────────────────────────────────── */}
      <div className="preview-section">
        <div className="preview-section-header">Color Palette</div>
        <div className="preview-section-body">
          <div className="preview-palette">
            {Object.entries(colors).map(([name, value]) => (
              <div key={name} className="palette-chip">
                <div
                  className="palette-swatch"
                  style={{ background: value }}
                  title={`${name}: ${value}`}
                />
                <div className="palette-name">{name}</div>
                <div style={{ fontSize: 8, color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Buttons ────────────────────────────────────────────────────────── */}
      <div className="preview-section">
        <div className="preview-section-header">Buttons</div>
        <div className="preview-section-body">
          <div className="preview-buttons">
            <button className="preview-btn preview-btn-primary">
              Primary
            </button>
            <button className="preview-btn preview-btn-secondary">
              Secondary
            </button>
            <button className="preview-btn preview-btn-ghost">
              Ghost
            </button>
            <button
              className="preview-btn preview-btn-primary"
              style={{ fontSize: 12, padding: "6px 14px" }}
            >
              Small
            </button>
            <button
              className="preview-btn preview-btn-primary"
              style={{ fontSize: 15, padding: "11px 26px" }}
            >
              Large
            </button>
            <button
              className="preview-btn preview-btn-primary"
              style={{ opacity: 0.4, cursor: "not-allowed" }}
              disabled
            >
              Disabled
            </button>
          </div>
        </div>
      </div>

      {/* ── Input Fields ───────────────────────────────────────────────────── */}
      <div className="preview-section">
        <div className="preview-section-header">Form Inputs</div>
        <div className="preview-section-body">
          <div className="preview-inputs">
            <div className="preview-field">
              <label className="preview-input-label">Default</label>
              <input
                className="preview-input"
                type="text"
                placeholder="Enter your email address"
                readOnly
              />
            </div>
            <div className="preview-field">
              <label className="preview-input-label">Focus State</label>
              <input
                className="preview-input"
                type="text"
                placeholder="Focused input"
                defaultValue="Active input"
                style={{
                  borderColor: "var(--preview-color-accent)",
                  boxShadow: "0 0 0 3px rgba(124,110,245,0.15)",
                }}
                readOnly
              />
            </div>
            <div className="preview-field">
              <label className="preview-input-label" style={{ color: "var(--danger)" }}>
                Error State
              </label>
              <input
                className="preview-input error"
                type="text"
                placeholder="Invalid value"
                defaultValue="incorrect@email"
                readOnly
              />
              <span style={{ fontSize: 10.5, color: "var(--danger)", marginTop: 3 }}>
                Please enter a valid email address.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Cards ──────────────────────────────────────────────────────────── */}
      <div className="preview-section">
        <div className="preview-section-header">Cards</div>
        <div className="preview-section-body">
          <div className="preview-cards">
            <div className="preview-card">
              <div className="preview-card-img" />
              <div className="preview-card-body">
                <div className="preview-card-title">Design Token</div>
                <div className="preview-card-desc">
                  Extracted from source with intelligent heuristics.
                </div>
                <button
                  className="preview-btn preview-btn-primary"
                  style={{ marginTop: 10, fontSize: 11, padding: "5px 12px" }}
                >
                  View →
                </button>
              </div>
            </div>
            <div
              className="preview-card"
              style={{ borderColor: "var(--preview-color-accent)" }}
            >
              <div className="preview-card-body" style={{ padding: 14 }}>
                <div style={{
                  fontSize: 24, fontWeight: 700,
                  color: "var(--preview-color-primary)",
                  fontFamily: "var(--preview-font-heading)",
                }}>
                  48
                </div>
                <div className="preview-card-title" style={{ marginTop: 4 }}>Components</div>
                <div className="preview-card-desc">Locked & versioned</div>
              </div>
            </div>
            <div
              className="preview-card"
              style={{ background: "var(--preview-color-primary)" }}
            >
              <div className="preview-card-body" style={{ padding: 14 }}>
                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.6)", marginBottom: 6 }}>
                  FEATURED
                </div>
                <div
                  className="preview-card-title"
                  style={{ color: "#fff", fontSize: 14 }}
                >
                  Brand Color
                </div>
                <div
                  className="preview-card-desc"
                  style={{ color: "rgba(255,255,255,0.65)" }}
                >
                  {colors.primary}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Typography Scale ────────────────────────────────────────────────── */}
      <div className="preview-section">
        <div className="preview-section-header">Typography Scale</div>
        <div className="preview-section-body">
          <div className="preview-type-scale">
            {[
              { tag: "h1", label: "H1", size: scale.h1?.size || "2.5rem", weight: scale.h1?.weight || "700" },
              { tag: "h2", label: "H2", size: scale.h2?.size || "2rem",   weight: scale.h2?.weight || "700" },
              { tag: "h3", label: "H3", size: scale.h3?.size || "1.75rem",weight: scale.h3?.weight || "600" },
              { tag: "h4", label: "H4", size: scale.h4?.size || "1.5rem", weight: scale.h4?.weight || "600" },
              { tag: "body",   label: "Body",    size: scale.body?.size   || "1rem",     weight: "400" },
              { tag: "small",  label: "Small",   size: scale.small?.size  || "0.875rem", weight: "400" },
              { tag: "caption",label: "Caption", size: scale.caption?.size|| "0.75rem",  weight: "400" },
            ].map(({ tag, label, size, weight }) => (
              <div key={tag} className="type-specimen">
                <span className="type-specimen-label">{label}</span>
                <span
                  className="type-specimen-text"
                  style={{
                    fontSize: size,
                    fontWeight: weight,
                    fontFamily: ["h1","h2","h3","h4"].includes(tag)
                      ? "var(--preview-font-heading)"
                      : "var(--preview-font-body)",
                  }}
                >
                  {tag === "h1" ? "Display Heading" :
                   tag === "h2" ? "Section Title" :
                   tag === "h3" ? "Subsection" :
                   tag === "h4" ? "Card Title" :
                   tag === "body" ? "Body text for reading" :
                   tag === "small" ? "Small supporting text" :
                   "Caption — metadata, labels"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Spacing Scale ───────────────────────────────────────────────────── */}
      {spacing?.named && (
        <div className="preview-section">
          <div className="preview-section-header">Spacing Rhythm</div>
          <div className="preview-section-body">
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end", flexWrap: "wrap" }}>
              {Object.entries(spacing.named).map(([name, val]) => {
                const px = parseInt(val) || 4;
                return (
                  <div key={name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                    <div style={{
                      width: px,
                      height: px,
                      background: "var(--preview-color-accent)",
                      borderRadius: 3,
                      opacity: 0.8,
                    }} />
                    <span style={{
                      fontSize: 9, color: "var(--text-muted)",
                      fontFamily: "var(--font-mono)", textAlign: "center"
                    }}>
                      {name}<br />{val}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Border Radius ───────────────────────────────────────────────────── */}
      {Object.keys(borderRadius).length > 0 && (
        <div className="preview-section">
          <div className="preview-section-header">Border Radius</div>
          <div className="preview-section-body">
            <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
              {Object.entries(borderRadius).map(([name, val]) => (
                <div key={name} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                  <div style={{
                    width: 48, height: 48,
                    background: "var(--preview-color-accent)",
                    borderRadius: val,
                    opacity: 0.85,
                  }} />
                  <span style={{ fontSize: 9, color: "var(--text-muted)", fontFamily: "var(--font-mono)", textAlign: "center" }}>
                    {name}<br />{val}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
