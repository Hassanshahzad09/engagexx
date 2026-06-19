import React, { useState } from "react";

const BASE_URL = "https://caddie-unlearned-author.ngrok-free.dev";

const LoginPage = () => {
  const [userId, setUserId] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);
  const [storedId, setStoredId] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!userId.trim()) {
      setError("Please enter a User ID");
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/auth/login/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });

      const data = await response.json();

      if (response.ok) {
        setLoggedIn(true);
        setStoredId(data.user_id);
        setError("");
      } else {
        setError(data.error || "Login failed");
      }
    } catch (err) {
      setError("Something went wrong. Try again.");
    }
  };

  const handleLogout = () => {
    setLoggedIn(false);
    setStoredId("");
    setUserId("");
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        {loggedIn ? (
          <>
            <div style={styles.successIcon}>OK</div>
            <h2 style={styles.title}>Welcome Back!</h2>
            <p style={styles.subtitle}>You are logged in as</p>
            <div style={styles.userIdBadge}>{storedId}</div>
            <p style={styles.hint}>You will stay logged in until you logout or refresh this test page.</p>
            <button onClick={handleLogout} style={styles.logoutButton}>
              Logout
            </button>
          </>
        ) : (
          <>
            <h2 style={styles.title}>Login to EngageX</h2>
            <p style={styles.subtitle}>Enter your User ID to get started</p>
            <input
              type="text"
              placeholder="Enter your User ID"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleLogin()}
              style={styles.input}
            />
            {error && <p style={styles.error}>{error}</p>}
            <button onClick={handleLogin} style={styles.loginButton}>
              Login
            </button>
          </>
        )}
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  wrapper: {
    minHeight: "100vh",
    background: "#0f0f13",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    background: "#1a1a24",
    border: "1px solid #2a2a3a",
    borderRadius: "20px",
    padding: "48px 40px",
    width: "380px",
    textAlign: "center",
  },
  successIcon: {
    width: "64px",
    height: "64px",
    background: "#22c55e",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 24px",
    fontSize: "20px",
    color: "white",
  },
  title: {
    color: "#f0f0f8",
    fontSize: "22px",
    fontWeight: "700",
    marginBottom: "10px",
  },
  subtitle: {
    color: "#6b6b85",
    fontSize: "14px",
    marginBottom: "24px",
  },
  userIdBadge: {
    background: "#2a2a3a",
    color: "#f0f0f8",
    padding: "12px 20px",
    borderRadius: "10px",
    fontSize: "16px",
    fontWeight: "600",
    marginBottom: "16px",
  },
  hint: {
    color: "#4a4a65",
    fontSize: "12px",
    marginBottom: "24px",
  },
  input: {
    width: "100%",
    padding: "14px 16px",
    background: "#0f0f13",
    border: "1px solid #2a2a3a",
    borderRadius: "12px",
    color: "#f0f0f8",
    fontSize: "15px",
    marginBottom: "16px",
    outline: "none",
    boxSizing: "border-box",
  },
  error: {
    color: "#ef4444",
    fontSize: "13px",
    marginBottom: "12px",
  },
  loginButton: {
    width: "100%",
    padding: "14px 20px",
    background: "#6366f1",
    color: "white",
    border: "none",
    borderRadius: "12px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
  },
  logoutButton: {
    width: "100%",
    padding: "14px 20px",
    background: "transparent",
    color: "#ef4444",
    border: "1px solid #ef4444",
    borderRadius: "12px",
    fontSize: "15px",
    fontWeight: "600",
    cursor: "pointer",
  },
};

export default LoginPage;
