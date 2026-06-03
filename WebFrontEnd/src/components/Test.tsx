import { useState } from "react";

function App() {
  const [platform, setPlatform] = useState("twitter");
  const [postUrl, setPostUrl] = useState("");
  const [maxComments, setMaxComments] = useState(30);

  const [checks, setChecks] = useState([
    {
      username: "",
      comment: "",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [error, setError] = useState("");

  const getApiUrl = () => {
    if (platform === "twitter") {
      return "http://127.0.0.1:8000/proof_checker/check-twitter-comments/";
    }

    if (platform === "instagram") {
      return "http://127.0.0.1:8000/proof_checker/check-instagram-comments/";
    }

    if (platform === "facebook") {
      return "http://127.0.0.1:8000/proof_checker/check-facebook-comments/";
    }

    if (platform === "youtube") {
      return "http://127.0.0.1:8000/proof_checker/check-youtube-comments/";
    }

    return "";
  };

  const platformLabel = {
    twitter: "Twitter / X",
    instagram: "Instagram",
    facebook: "Facebook",
    youtube: "YouTube",
  }[platform];

  const getUrlPlaceholder = () => {
    if (platform === "twitter") {
      return "https://x.com/username/status/123456";
    }

    if (platform === "instagram") {
      return "https://www.instagram.com/p/post_id/";
    }

    if (platform === "facebook") {
      return "https://www.facebook.com/permalink.php?story_fbid=...&id=...";
    }

    if (platform === "youtube") {
      return "https://www.youtube.com/watch?v=video_id";
    }

    return "Enter post URL";
  };

  const getLoadingText = () => {
    if (platform === "twitter") {
      return "Twitter browser may ask manual login. Complete it and press Enter in terminal.";
    }

    if (platform === "instagram") {
      return "Instagram uses saved session. If expired, run save_instagram_session again.";
    }

    if (platform === "facebook") {
      return "Facebook post is being scraped. If captcha appears, complete it manually.";
    }

    if (platform === "youtube") {
      return "YouTube video comments are loading. No login is usually required.";
    }

    return "Scraping started...";
  };

  const addCheckRow = () => {
    setChecks([
      ...checks,
      {
        username: "",
        comment: "",
      },
    ]);
  };

  const removeCheckRow = (index) => {
    if (checks.length === 1) {
      setError("At least one username/comment row is required.");
      return;
    }

    const updated = checks.filter((_, i) => i !== index);
    setChecks(updated);
  };

  const updateCheck = (index, field, value) => {
    const updated = [...checks];
    updated[index][field] = value;
    setChecks(updated);
  };

  const resetForm = () => {
    setPostUrl("");
    setMaxComments(30);
    setChecks([
      {
        username: "",
        comment: "",
      },
    ]);
    setApiResult(null);
    setError("");
  };

  const submitProofCheck = async () => {
    setLoading(true);
    setApiResult(null);
    setError("");

    if (!postUrl.trim()) {
      setError("Please enter post/video URL.");
      setLoading(false);
      return;
    }

    if (!maxComments || Number(maxComments) <= 0) {
      setError("Please enter valid number of comments/replies to scrape.");
      setLoading(false);
      return;
    }

    const validChecks = checks.filter(
      (item) => item.username.trim() && item.comment.trim()
    );

    if (validChecks.length === 0) {
      setError("Please enter at least one username and comment.");
      setLoading(false);
      return;
    }

    try {
      const apiUrl = getApiUrl();

      let payload = {
        checks: validChecks,
      };

      if (platform === "twitter") {
        payload = {
          ...payload,
          tweet_url: postUrl,
          max_replies: Number(maxComments),
        };
      }

      if (platform === "instagram") {
        payload = {
          ...payload,
          post_url: postUrl,
          max_comments: Number(maxComments),
        };
      }

      if (platform === "facebook") {
        payload = {
          ...payload,
          post_url: postUrl,
          max_comments: Number(maxComments),
        };
      }

      if (platform === "youtube") {
        payload = {
          ...payload,
          video_url: postUrl,
          max_comments: Number(maxComments),
        };
      }

      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (!data.success) {
        setError(data.message || "Something went wrong.");
        setLoading(false);
        return;
      }

      setApiResult(data);
    } catch (err) {
      setError("Backend is not running or API URL is wrong.");
    }

    setLoading(false);
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>EngageX Proof Checker</h1>
            <p style={styles.subtitle}>
              Check seller comments from Twitter/X, Instagram, Facebook, and YouTube.
            </p>
          </div>

          <div style={styles.badge}>{platformLabel}</div>
        </div>

        <div style={styles.section}>
          <label style={styles.label}>Select Platform</label>

          <select
            style={styles.input}
            value={platform}
            onChange={(e) => {
              setPlatform(e.target.value);
              setApiResult(null);
              setError("");
            }}
          >
            <option value="twitter">Twitter / X</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
            <option value="youtube">YouTube</option>
          </select>
        </div>

        <div style={styles.section}>
          <label style={styles.label}>
            {platform === "youtube" ? "Video URL" : "Post URL"}
          </label>

          <input
            style={styles.input}
            type="text"
            placeholder={getUrlPlaceholder()}
            value={postUrl}
            onChange={(e) => setPostUrl(e.target.value)}
          />

          {platform === "instagram" && (
            <p style={styles.hint}>
              Backend will automatically clean the URL and use{" "}
              <strong>/comments/</strong>.
            </p>
          )}

          {platform === "facebook" && (
            <p style={styles.hint}>
              Use a public Facebook post URL. Backend will handle Facebook URL layout.
            </p>
          )}

          {platform === "youtube" && (
            <p style={styles.hint}>
              Use a public YouTube video URL. Backend will scroll until comments load.
            </p>
          )}
        </div>

        <div style={styles.section}>
          <label style={styles.label}>
            How many comments/replies do you want to scrape?
          </label>

          <input
            style={styles.input}
            type="number"
            min="1"
            value={maxComments}
            onChange={(e) => setMaxComments(e.target.value)}
          />
        </div>

        <div style={styles.checksHeader}>
          <h2 style={styles.sectionTitle}>Users & Comments to Check</h2>

          <button style={styles.addButton} onClick={addCheckRow}>
            + Add User
          </button>
        </div>

        {checks.map((item, index) => (
          <div key={index} style={styles.checkCard}>
            <div style={styles.checkTop}>
              <h3 style={styles.checkTitle}>Check #{index + 1}</h3>

              <button
                style={styles.removeButton}
                onClick={() => removeCheckRow(index)}
              >
                Remove
              </button>
            </div>

            <div style={styles.section}>
              <label style={styles.label}>Username / Name</label>

              <input
                style={styles.input}
                type="text"
                placeholder={
                  platform === "facebook" || platform === "youtube"
                    ? "Profile/channel/commenter name"
                    : "@username"
                }
                value={item.username}
                onChange={(e) =>
                  updateCheck(index, "username", e.target.value)
                }
              />
            </div>

            <div style={styles.section}>
              <label style={styles.label}>Comment</label>

              <textarea
                style={styles.textarea}
                placeholder="Enter seller submitted comment..."
                value={item.comment}
                onChange={(e) =>
                  updateCheck(index, "comment", e.target.value)
                }
              />
            </div>
          </div>
        ))}

        <div style={styles.buttonRow}>
          <button
            style={{
              ...styles.primaryButton,
              opacity: loading ? 0.7 : 1,
              cursor: loading ? "not-allowed" : "pointer",
            }}
            onClick={submitProofCheck}
            disabled={loading}
          >
            {loading ? "Scraping & Checking..." : "Scrape & Check All"}
          </button>

          <button style={styles.secondaryButton} onClick={resetForm}>
            Reset
          </button>
        </div>

        {loading && (
          <div style={styles.loadingBox}>
            <div style={styles.spinner}></div>

            <div>
              <h3 style={styles.loadingTitle}>Scraping started...</h3>
              <p style={styles.loadingText}>{getLoadingText()}</p>
            </div>
          </div>
        )}

        {error && (
          <div style={styles.errorBox}>
            <h3 style={styles.errorTitle}>Error</h3>
            <p style={styles.errorText}>{error}</p>
          </div>
        )}

        {apiResult && (
          <div style={styles.resultBox}>
            <div style={styles.resultHeader}>
              <div>
                <h2 style={styles.resultMainTitle}>Final Result</h2>

                <p style={styles.resultSubText}>
                  Platform: {apiResult.platform}
                </p>

                <p style={styles.resultSubText}>
                  Comments Checked: {apiResult.total_comments_checked}
                </p>
              </div>

              <div style={styles.totalBadge}>
                {apiResult.results?.filter((r) => r.comment_found).length || 0} /{" "}
                {apiResult.results?.length || 0} Valid
              </div>
            </div>

            <div style={styles.resultList}>
              {apiResult.results?.map((item, index) => (
                <div
                  key={index}
                  style={
                    item.comment_found
                      ? styles.validResultCard
                      : styles.invalidResultCard
                  }
                >
                  <div style={styles.resultCardTop}>
                    <h3 style={styles.resultUser}>{item.username}</h3>

                    <span
                      style={
                        item.comment_found
                          ? styles.validSmallBadge
                          : styles.invalidSmallBadge
                      }
                    >
                      {item.comment_found ? "VALID" : "INVALID"}
                    </span>
                  </div>

                  <p style={styles.submittedComment}>
                    <strong>Submitted Comment:</strong> {item.comment}
                  </p>

                  {item.matched_comment && (
                    <div style={styles.matchBox}>
                      <p style={styles.matchUser}>
                        Matched User: @{item.matched_comment.username}
                      </p>

                      <p style={styles.matchComment}>
                        {item.matched_comment.comment}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={styles.seenBox}>
              <h3 style={styles.seenTitle}>Comments Seen by Scraper</h3>

              {apiResult.seen_comments && apiResult.seen_comments.length > 0 ? (
                apiResult.seen_comments.map((item, index) => (
                  <div key={index} style={styles.seenComment}>
                    <div style={styles.seenTop}>
                      <p style={styles.seenUser}>@{item.username}</p>

                      {(item.likes || item.published) && (
                        <p style={styles.seenMeta}>
                          {item.likes ? `Likes: ${item.likes}` : ""}
                          {item.likes && item.published ? " | " : ""}
                          {item.published ? item.published : ""}
                        </p>
                      )}
                    </div>

                    <p style={styles.seenText}>{item.comment}</p>
                  </div>
                ))
              ) : (
                <p style={styles.noSeenText}>
                  No comments were scraped from this post/video.
                </p>
              )}
            </div>
          </div>
        )}
      </div>

      <style>
        {`
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }

          input:focus,
          textarea:focus,
          select:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
          }

          button:hover {
            transform: translateY(-1px);
          }

          @media (max-width: 700px) {
            .responsive-header {
              flex-direction: column;
            }
          }
        `}
      </style>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    background:
      "linear-gradient(135deg, #eef2ff 0%, #f8fafc 45%, #e0f2fe 100%)",
    display: "flex",
    justifyContent: "center",
    alignItems: "flex-start",
    padding: "35px",
    fontFamily:
      "Inter, Arial, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
  },

  card: {
    width: "100%",
    maxWidth: "920px",
    background: "#ffffff",
    borderRadius: "24px",
    padding: "30px",
    boxShadow: "0 25px 80px rgba(15, 23, 42, 0.12)",
    border: "1px solid #e2e8f0",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    gap: "20px",
    alignItems: "flex-start",
    marginBottom: "28px",
  },

  title: {
    margin: 0,
    color: "#0f172a",
    fontSize: "32px",
    fontWeight: "800",
  },

  subtitle: {
    marginTop: "8px",
    color: "#64748b",
    fontSize: "15px",
    lineHeight: "1.5",
  },

  badge: {
    background: "#dbeafe",
    color: "#1d4ed8",
    padding: "8px 14px",
    borderRadius: "999px",
    fontWeight: "800",
    fontSize: "13px",
    whiteSpace: "nowrap",
  },

  section: {
    marginBottom: "18px",
  },

  label: {
    display: "block",
    color: "#334155",
    fontWeight: "700",
    marginBottom: "8px",
    fontSize: "14px",
  },

  input: {
    width: "100%",
    padding: "14px 15px",
    borderRadius: "12px",
    border: "1px solid #cbd5e1",
    outline: "none",
    fontSize: "15px",
    background: "#ffffff",
    color: "#0f172a",
    boxSizing: "border-box",
  },

  textarea: {
    width: "100%",
    minHeight: "95px",
    padding: "14px 15px",
    borderRadius: "12px",
    border: "1px solid #cbd5e1",
    outline: "none",
    fontSize: "15px",
    background: "#ffffff",
    color: "#0f172a",
    resize: "vertical",
    boxSizing: "border-box",
  },

  hint: {
    marginTop: "6px",
    color: "#64748b",
    fontSize: "13px",
  },

  checksHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "10px",
    marginBottom: "15px",
    gap: "12px",
  },

  sectionTitle: {
    margin: 0,
    color: "#0f172a",
    fontSize: "22px",
  },

  addButton: {
    border: "none",
    background: "#2563eb",
    color: "white",
    padding: "11px 16px",
    borderRadius: "10px",
    fontWeight: "800",
    cursor: "pointer",
    whiteSpace: "nowrap",
  },

  checkCard: {
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "18px",
    padding: "18px",
    marginBottom: "16px",
  },

  checkTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "12px",
  },

  checkTitle: {
    margin: 0,
    color: "#0f172a",
    fontSize: "18px",
  },

  removeButton: {
    border: "1px solid #fecaca",
    background: "#fee2e2",
    color: "#991b1b",
    padding: "8px 12px",
    borderRadius: "10px",
    fontWeight: "700",
    cursor: "pointer",
  },

  buttonRow: {
    display: "flex",
    gap: "12px",
    marginTop: "20px",
  },

  primaryButton: {
    flex: 1,
    border: "none",
    background: "linear-gradient(135deg, #2563eb, #1d4ed8)",
    color: "white",
    padding: "15px 18px",
    borderRadius: "12px",
    fontWeight: "800",
    fontSize: "15px",
  },

  secondaryButton: {
    border: "1px solid #cbd5e1",
    background: "#ffffff",
    color: "#334155",
    padding: "15px 18px",
    borderRadius: "12px",
    fontWeight: "800",
    fontSize: "15px",
    cursor: "pointer",
  },

  loadingBox: {
    marginTop: "20px",
    display: "flex",
    alignItems: "center",
    gap: "14px",
    background: "#eff6ff",
    border: "1px solid #bfdbfe",
    borderRadius: "16px",
    padding: "18px",
  },

  spinner: {
    width: "28px",
    height: "28px",
    border: "4px solid #bfdbfe",
    borderTop: "4px solid #2563eb",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    flexShrink: 0,
  },

  loadingTitle: {
    margin: 0,
    color: "#1e40af",
    fontSize: "16px",
  },

  loadingText: {
    margin: "4px 0 0",
    color: "#1d4ed8",
    fontSize: "14px",
    lineHeight: "1.5",
  },

  errorBox: {
    marginTop: "20px",
    background: "#fee2e2",
    border: "1px solid #fecaca",
    color: "#991b1b",
    borderRadius: "16px",
    padding: "18px",
  },

  errorTitle: {
    margin: 0,
    fontSize: "17px",
  },

  errorText: {
    margin: "6px 0 0",
    fontSize: "14px",
  },

  resultBox: {
    marginTop: "25px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "18px",
    padding: "20px",
  },

  resultHeader: {
    display: "flex",
    justifyContent: "space-between",
    gap: "15px",
    alignItems: "center",
    marginBottom: "18px",
  },

  resultMainTitle: {
    margin: 0,
    color: "#0f172a",
    fontSize: "25px",
  },

  resultSubText: {
    margin: "6px 0 0",
    color: "#64748b",
    fontSize: "14px",
  },

  totalBadge: {
    background: "#0f172a",
    color: "#ffffff",
    padding: "10px 14px",
    borderRadius: "999px",
    fontWeight: "800",
    fontSize: "13px",
    whiteSpace: "nowrap",
  },

  resultList: {
    display: "grid",
    gap: "14px",
  },

  validResultCard: {
    background: "#dcfce7",
    border: "1px solid #bbf7d0",
    color: "#166534",
    borderRadius: "16px",
    padding: "16px",
  },

  invalidResultCard: {
    background: "#fee2e2",
    border: "1px solid #fecaca",
    color: "#991b1b",
    borderRadius: "16px",
    padding: "16px",
  },

  resultCardTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
  },

  resultUser: {
    margin: 0,
    fontSize: "18px",
  },

  validSmallBadge: {
    background: "#16a34a",
    color: "#ffffff",
    padding: "6px 10px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: "800",
  },

  invalidSmallBadge: {
    background: "#dc2626",
    color: "#ffffff",
    padding: "6px 10px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: "800",
  },

  submittedComment: {
    marginTop: "12px",
    marginBottom: 0,
    lineHeight: "1.5",
  },

  matchBox: {
    marginTop: "12px",
    background: "#ffffff",
    color: "#0f172a",
    padding: "14px",
    borderRadius: "12px",
    border: "1px solid rgba(203, 213, 225, 0.8)",
  },

  matchUser: {
    margin: 0,
    color: "#2563eb",
    fontWeight: "800",
  },

  matchComment: {
    margin: "8px 0 0",
    color: "#334155",
    lineHeight: "1.5",
    whiteSpace: "pre-wrap",
  },

  seenBox: {
    marginTop: "22px",
    background: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "16px",
    padding: "18px",
  },

  seenTitle: {
    margin: 0,
    color: "#0f172a",
    fontSize: "19px",
  },

  seenComment: {
    marginTop: "12px",
    background: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "12px",
    padding: "13px",
  },

  seenTop: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
    alignItems: "center",
  },

  seenUser: {
    margin: 0,
    color: "#2563eb",
    fontWeight: "800",
  },

  seenMeta: {
    margin: 0,
    color: "#64748b",
    fontSize: "12px",
  },

  seenText: {
    margin: "7px 0 0",
    color: "#334155",
    lineHeight: "1.5",
    whiteSpace: "pre-wrap",
  },

  noSeenText: {
    color: "#64748b",
    marginTop: "12px",
  },
};

export default App;