import React, { useState, useEffect } from "react";

const BASE_URL = "http://127.0.0.1:8000";

interface PlatformStatus {
  connected: boolean;
  username: string | null;
}

interface Connections {
  facebook: PlatformStatus;
  instagram: PlatformStatus;
  twitter: PlatformStatus;
  youtube: PlatformStatus;
}

type Platform = keyof Connections;

const PLATFORMS: {
  key: Platform;
  label: string;
  brand: string;
  brandHover: string;
  path: string;
  icon: React.ReactNode;
}[] = [
  {
    key: "facebook",
    label: "Facebook",
    brand: "#1877F2",
    brandHover: "#0e66d0",
    path: "facebook",
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M24 12.073C24 5.404 18.627 0 12 0S0 5.404 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.235 2.686.235v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" />
      </svg>
    ),
  },
  {
    key: "instagram",
    label: "Instagram",
    brand: "linear-gradient(45deg,#f09433,#e6683c,#dc2743,#cc2366,#bc1888)",
    brandHover: "linear-gradient(45deg,#e08323,#d6582c,#cc1733,#bc1356,#ac0878)",
    path: "instagram",
    icon: (
      <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
  },
  {
    key: "twitter",
    label: "X",
    brand: "#000000",
    brandHover: "#1a1a1a",
    path: "twitter",
    icon: (
      <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  {
    key: "youtube",
    label: "YouTube",
    brand: "#FF0000",
    brandHover: "#cc0000",
    path: "youtube",
    icon: (
      <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
  },
];

const ConnectSocial: React.FC = () => {
  const [connections, setConnections] = useState<Connections>({
    facebook: { connected: false, username: null },
    instagram: { connected: false, username: null },
    twitter: { connected: false, username: null },
    youtube: { connected: false, username: null },
  });
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<Platform | null>(null);
  const [hovered, setHovered] = useState<Platform | null>(null);
  const [tooltip, setTooltip] = useState<Platform | null>(null);

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/connections/`);
      const data = await response.json();
      setConnections(data);
    } catch (err) {
      console.error("Failed to fetch connections");
    } finally {
      setLoading(false);
    }
  };

  const connect = (platform: Platform, path: string) => {
    setPending(platform);
    window.location.href = `${BASE_URL}/oauth/${path}/`;
  };

  const disconnect = async (platform: Platform) => {
    try {
      setPending(platform);
      await fetch(`${BASE_URL}/api/disconnect/${platform}/`, { method: "DELETE" });
      await fetchConnections();
    } catch (err) {
      console.error("Failed to disconnect");
    } finally {
      setPending(null);
    }
  };

  const handleClick = (platform: Platform, path: string) => {
    if (pending) return;
    if (connections[platform].connected) {
      disconnect(platform);
    } else {
      connect(platform, path);
    }
  };

  return (
    <div style={styles.bar}>
      {PLATFORMS.map((p) => {
        const isConnected = connections[p.key].connected;
        const isHovered = hovered === p.key;
        const isPending = pending === p.key;
        const showTooltip = tooltip === p.key;

        const brandSolid =
          typeof p.brand === "string" && p.brand.startsWith("#") ? p.brand : "#dc2743";

        const bg = isConnected
          ? isHovered
            ? p.brandHover
            : p.brand
          : "transparent";

        const color = isConnected ? "#fff" : isHovered ? brandSolid : "#9aa0b4";
        const borderColor = isConnected
          ? "transparent"
          : isHovered
          ? brandSolid
          : "rgba(255,255,255,0.18)";

        const tooltipText = loading
          ? "Checking..."
          : isPending
          ? isConnected
            ? "Disconnecting..."
            : "Redirecting..."
          : isConnected
          ? `${p.label} • ${connections[p.key].username ?? "connected"} — click to disconnect`
          : `Connect ${p.label}`;

        return (
          <div key={p.key} style={styles.itemWrap}>
            <button
              type="button"
              aria-label={tooltipText}
              disabled={loading || isPending}
              onMouseEnter={() => {
                setHovered(p.key);
                setTooltip(p.key);
              }}
              onMouseLeave={() => {
                setHovered((h) => (h === p.key ? null : h));
                setTooltip((t) => (t === p.key ? null : t));
              }}
              onFocus={() => setTooltip(p.key)}
              onBlur={() => setTooltip((t) => (t === p.key ? null : t))}
              onClick={() => handleClick(p.key, p.path)}
              style={{
                ...styles.iconBtn,
                background: bg,
                color,
                border: `1px solid ${borderColor}`,
                transform: isHovered && !isPending ? "translateY(-1px) scale(1.05)" : "translateY(0) scale(1)",
                boxShadow: isConnected
                  ? `0 4px 14px -4px ${typeof p.brand === "string" && p.brand.startsWith("#") ? p.brand : "rgba(220,39,67,0.5)"}`
                  : "0 1px 2px rgba(0,0,0,0.2)",
                cursor: loading || isPending ? "wait" : "pointer",
                opacity: loading ? 0.6 : 1,
              }}
            >
              <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                {p.icon}
              </span>
              {isConnected && (
                <span style={styles.dot} aria-hidden>
                  <span style={styles.dotInner} />
                </span>
              )}
            </button>
            {showTooltip && (
              <div role="tooltip" style={styles.tooltip}>
                {tooltipText}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  bar: {
    display: "inline-flex",
    alignItems: "center",
    gap: "16px",
    padding: 0,
    background: "transparent",
    border: "none",
  },
  itemWrap: {
    position: "relative",
    display: "inline-flex",
  },
  iconBtn: {
    position: "relative",
    width: "48px",
    height: "48px",
    borderRadius: "50%",
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 0,
    transition:
      "background 180ms ease, color 180ms ease, transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease",
    outline: "none",
  },
  dot: {
    position: "absolute",
    top: "-2px",
    right: "-2px",
    width: "10px",
    height: "10px",
    borderRadius: "50%",
    background: "#0f0f13",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  dotInner: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    background: "#22c55e",
    boxShadow: "0 0 6px #22c55e",
  },
  tooltip: {
    position: "absolute",
    top: "calc(100% + 8px)",
    left: "50%",
    transform: "translateX(-50%)",
    background: "#1a1a24",
    color: "#f0f0f8",
    border: "1px solid #2a2a3a",
    padding: "6px 10px",
    borderRadius: "8px",
    fontSize: "11px",
    whiteSpace: "nowrap",
    pointerEvents: "none",
    zIndex: 50,
    boxShadow: "0 6px 20px rgba(0,0,0,0.4)",
  },
};

export default ConnectSocial;
