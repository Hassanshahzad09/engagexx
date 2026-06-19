import React, { useState, useEffect } from "react";

const BASE_URL = "https://caddie-unlearned-author.ngrok-free.dev";

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

interface PlatformDef {
  key: Platform;
  label: string;
  /** modern connected background (solid color or gradient) */
  bg: string;
  bgHover: string;
  /** brand accent used for the icon when not connected */
  accent: string;
  path: string;
  icon: React.ReactNode;
}

const PLATFORMS: PlatformDef[] = [
  {
    key: "facebook",
    label: "Facebook",
    bg: "#0866FF",
    bgHover: "#0a5de0",
    accent: "#0866FF",
    path: "facebook",
    icon: (
      <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
        <path d="M24 12.073C24 5.404 18.627 0 12 0S0 5.404 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.41c0-3.025 1.792-4.697 4.533-4.697 1.312 0 2.686.235 2.686.235v2.97h-1.513c-1.491 0-1.956.93-1.956 1.886v2.268h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" />
      </svg>
    ),
  },
  {
    key: "instagram",
    label: "Instagram",
    bg: "linear-gradient(135deg,#7638FA 0%,#E1306C 50%,#FFB400 100%)",
    bgHover: "linear-gradient(135deg,#6a2be8 0%,#d32861 50%,#f0a800 100%)",
    accent: "#E1306C",
    path: "instagram",
    icon: (
      <svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
  },
  {
    key: "twitter",
    label: "X",
    bg: "#0F1419",
    bgHover: "#000000",
    accent: "#0F1419",
    path: "twitter",
    icon: (
      <svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.259 5.63 5.905-5.63zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  {
    key: "youtube",
    label: "YouTube",
    bg: "#FF0033",
    bgHover: "#e6002e",
    accent: "#FF0033",
    path: "youtube",
    icon: (
      <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
        <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
      </svg>
    ),
  },
];

interface Props {
  connectedPlatforms: {
    facebook: boolean;
    instagram: boolean;
    twitter: boolean;
    youtube: boolean;
  };
  setConnectedPlatforms: React.Dispatch<
    React.SetStateAction<{
      facebook: boolean;
      instagram: boolean;
      twitter: boolean;
      youtube: boolean;
    }>
  >;
  sellerId: string | number;
  theme?: string;
}

const ConnectSocial: React.FC<Props> = ({
  connectedPlatforms,
  setConnectedPlatforms,
  sellerId,
  theme = "light",
}) => {
  const isDark = theme === "dark";
  const [connections, setConnections] = useState<Connections>({
    facebook: { connected: false, username: null },
    instagram: { connected: false, username: null },
    twitter: { connected: false, username: null },
    youtube: { connected: false, username: null },
  });
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<Platform | null>(null);
  const [hovered, setHovered] = useState<Platform | null>(null);

  useEffect(() => {
    fetchConnections();
  }, [sellerId]);

  /*
  const fetchConnections = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/connections?sellerId=${sellerId}`);
      const data = await response.json();
      setConnections(data);
      setConnectedPlatforms({
        facebook: data.facebook.connected,
        instagram: data.instagram.connected,
        twitter: data.twitter.connected,
        youtube: data.youtube.connected,
      });
    } catch (err) {
      console.error("Failed to fetch connections");
    } finally {
      setLoading(false);
    }
  };
*/

const fetchConnections = async () => {
  try {

    const response = await fetch(
      `${BASE_URL}/api/connections/?sellerId=${sellerId}`
    );

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to fetch connections");
    }

    // compare old vs new
    const hasChanged =
      JSON.stringify(connections) !== JSON.stringify(data);

    // only update if changed
    if (hasChanged) {

      setConnections(data);

      setConnectedPlatforms({
        facebook: data.facebook.connected,
        instagram: data.instagram.connected,
        twitter: data.twitter.connected,
        youtube: data.youtube.connected,
      });

      console.log("Connections updated");
    }

  } catch (err) {

    console.error("Failed to fetch connections");

  } finally {

    setLoading(false);

  }
};
  const connect = (platform: Platform, path: string) => {
    setPending(platform);
    const popup = window.open(
      `${BASE_URL}/oauth/${path}/?seller_id=${sellerId}`,
      "OAuthLogin",
      "width=500,height=600,scrollbars=yes,resizable=yes"
    );

    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== BASE_URL) return;

      // OAuth succeeded — refresh connections
      fetchConnections();
      
      popup?.close();
      setPending(null);
      window.removeEventListener("message", handleMessage);
    };

    window.addEventListener("message", handleMessage);

    // Fallback: if user closes popup manually without completing OAuth
    const pollClosed = setInterval(() => {
      if (popup?.closed) {
        clearInterval(pollClosed);
        window.removeEventListener("message", handleMessage);
        fetchConnections();
        setPending(null);
      }
    }, 500);
  };

  const disconnect = async (platform: Platform) => {
    try {
      setPending(platform);
      await fetch(`${BASE_URL}/api/disconnect/${platform}/?sellerId=${sellerId}`, { method: "DELETE" });
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
    <div style={styles.wrapper}>
      <div style={styles.header}>
        <div style={styles.title}>Platform Connections</div>
        <div style={styles.subtitle}>
          Connect your social media accounts to unlock tasks
        </div>
      </div>

      <div style={styles.grid}>
        {PLATFORMS.map((p) => {
          const isConnected = connections[p.key].connected;
          const isHovered = hovered === p.key;
          const isPending = pending === p.key;
          const unconnectedBg = isDark
            ? isHovered
              ? "#303132"
              : "#242526"
            : "#ffffff";
          const unconnectedBorder = isDark
            ? isHovered
              ? p.accent
              : "#3a3b3c"
            : isHovered
            ? p.accent
            : "#e5e7eb";
          const unconnectedText = isDark ? "#e4e6eb" : "#111827";
          const unconnectedStatus = isDark ? "#b0b3b8" : "#6b7280";
          const unconnectedIcon =
            isDark && p.key === "twitter" ? "#e4e6eb" : p.accent;

          const cardStyle: React.CSSProperties = {
            ...styles.card,
            background: isConnected ? (isHovered ? p.bgHover : p.bg) : unconnectedBg,
            border: isConnected
              ? "1px solid transparent"
              : `1px solid ${unconnectedBorder}`,
            color: isConnected ? "#ffffff" : unconnectedText,
            transform: isHovered && !isPending ? "translateY(-3px)" : "translateY(0)",
            boxShadow: isConnected
              ? isHovered
                ? `0 14px 30px -10px ${p.accent}80`
                : `0 8px 22px -10px ${p.accent}66`
              : isHovered
              ? `0 12px 26px -12px ${p.accent}80`
              : isDark
              ? "0 10px 24px rgba(0,0,0,0.24)"
              : "0 1px 2px rgba(0,0,0,0.04)",
            cursor: loading || isPending ? "wait" : "pointer",
            opacity: loading ? 0.6 : 1,
          };

          const iconColor = isConnected ? "#ffffff" : unconnectedIcon;
          const statusText = loading
            ? "Checking..."
            : isPending
            ? isConnected
              ? "Disconnecting..."
              : "Connecting..."
            : isConnected
            ? "Connected"
            : "Not Connected";

          return (
            <button
              key={p.key}
              type="button"
              disabled={loading || isPending}
              onMouseEnter={() => setHovered(p.key)}
              onMouseLeave={() => setHovered((h) => (h === p.key ? null : h))}
              onClick={() => handleClick(p.key, p.path)}
              style={cardStyle}
              aria-label={`${p.label} - ${statusText}`}
            >
              <span style={{ ...styles.iconBox, color: iconColor }}>{p.icon}</span>
              <span style={styles.label}>{p.label}</span>
              <span
                style={{
                  ...styles.status,
                  color: isConnected ? "rgba(255,255,255,0.92)" : unconnectedStatus,
                }}
              >
                {statusText}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  wrapper: {
    width: "100%",
    background: "var(--connect-panel-bg)",
    border: "1px solid var(--connect-panel-border)",
    borderRadius: "16px",
    padding: "20px 22px 22px",
    boxShadow: "var(--connect-panel-shadow)",
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Inter, Helvetica, Arial, sans-serif",
  },
  header: {
    marginBottom: "16px",
  },
  title: {
    fontSize: "15px",
    fontWeight: 600,
    color: "var(--connect-title)",
    letterSpacing: "0.1px",
  },
  subtitle: {
    fontSize: "13px",
    color: "var(--connect-subtitle)",
    marginTop: "2px",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "14px",
  },
  card: {
    appearance: "none",
    WebkitAppearance: "none",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    padding: "20px 16px",
    borderRadius: "12px",
    transition:
      "background 220ms ease, color 220ms ease, transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease",
    outline: "none",
    minHeight: "120px",
  },
  iconBox: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    height: "30px",
    transition: "color 220ms ease",
  },
  label: {
    fontSize: "15px",
    fontWeight: 600,
    letterSpacing: "0.1px",
  },
  status: {
    fontSize: "12px",
    fontWeight: 500,
  },
};

export default ConnectSocial;
