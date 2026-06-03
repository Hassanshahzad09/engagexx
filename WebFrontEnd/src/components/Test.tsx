import { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000/api/fraud-stats/";

/*
  IMPORTANT:
  Ye action URL tum apne Django backend ke according set karna.
  Is endpoint ka kaam hoga admin ka action save karna:
  VALID_PROOF, INVALID_PROOF, AUDIT_PASSED, AUDIT_FAILED
*/
const ACTION_API_URL = "http://127.0.0.1:8000/api/admin-task-action/";

export default function App() {
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);

  const [loading, setLoading] = useState(false);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [error, setError] = useState("");

  const [openedCardId, setOpenedCardId] = useState(null);
  const [selectedFilter, setSelectedFilter] = useState("ALL");

  const fetchFraudTasks = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(API_URL);

      if (!response.ok) {
        throw new Error("Failed to fetch fraud tasks");
      }

      const data = await response.json();

      setSummary(data.summary || null);
      setResults(data.results || []);
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFraudTasks();
  }, []);

  const handleAdminAction = async (item, actionType) => {
    try {
      setActionLoadingId(item.id);

      /*
        Backend ko ye data send hoga.
        Tum Django me is action ko receive karke task/proof/audit status update kar sakte ho.
      */
      const payload = {
        analysis_id: item.id,
        task_id: item.task_id,
        seller_id: item.seller_id,
        action: actionType,
      };

      const response = await fetch(ACTION_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error("Admin action failed");
      }

      /*
        UI ko immediately update kar rahe hain taake admin ko result dikh jaye.
      */
      setResults((prevResults) =>
        prevResults.map((task) => {
          if (task.id !== item.id) return task;

          if (actionType === "VALID_PROOF") {
            return {
              ...task,
              proof_status: "valid",
            };
          }

          if (actionType === "INVALID_PROOF") {
            return {
              ...task,
              proof_status: "invalid",
            };
          }

          if (actionType === "AUDIT_PASSED") {
            return {
              ...task,
              audit_status: "passed",
            };
          }

          if (actionType === "AUDIT_FAILED") {
            return {
              ...task,
              audit_status: "failed",
            };
          }

          return task;
        })
      );
    } catch (err) {
      alert(err.message || "Action failed");
    } finally {
      setActionLoadingId(null);
    }
  };

  const filteredResults = results.filter((item) => {
    if (selectedFilter === "ALL") return true;
    if (selectedFilter === "FRAUD") return item.is_fraud === true;
    if (selectedFilter === "LOW") return item.risk_level === "LOW";
    if (selectedFilter === "MEDIUM") return item.risk_level === "MEDIUM";
    if (selectedFilter === "HIGH") return item.risk_level === "HIGH";
    if (selectedFilter === "CRITICAL") return item.risk_level === "CRITICAL";
    return true;
  });

  return (
    <div style={styles.page}>
      <div style={styles.topBar}>
        <div>
          <h1 style={styles.title}>Admin Task Review</h1>
          <p style={styles.subtitle}>
            Review seller proof, fraud risk, suspicious signals, and approve or reject tasks.
          </p>
        </div>

        <button style={styles.refreshBtn} onClick={fetchFraudTasks}>
          Refresh
        </button>
      </div>

      {error && <div style={styles.errorBox}>{error}</div>}

      {loading && <div style={styles.loadingBox}>Loading tasks...</div>}

      {summary && (
        <div style={styles.statsGrid}>
          <StatBox label="Total" value={summary.total || 0} color="#047857" />
          <StatBox label="Fraud" value={summary.fraud || 0} color="#dc2626" />
          <StatBox label="Legit" value={summary.legitimate || 0} color="#16a34a" />
          <StatBox
            label="Avg Probability"
            value={`${summary.avg_probability || 0}%`}
            color="#d97706"
          />
        </div>
      )}

      <div style={styles.filterBar}>
        {["ALL", "FRAUD", "LOW", "MEDIUM", "HIGH", "CRITICAL"].map((filter) => (
          <button
            key={filter}
            style={{
              ...styles.filterBtn,
              ...(selectedFilter === filter ? styles.activeFilterBtn : {}),
            }}
            onClick={() => setSelectedFilter(filter)}
          >
            {filter}
          </button>
        ))}
      </div>

      <div style={styles.taskList}>
        {filteredResults.length === 0 && !loading ? (
          <div style={styles.emptyBox}>No task found.</div>
        ) : (
          filteredResults.map((item) => {
            const fraudProbability = Number(item.fraud_probability || 0);
            const isOpen = openedCardId === item.id;
            const signals = Array.isArray(item.suspicious_signals)
              ? item.suspicious_signals
              : [];

            return (
              <div key={item.id} style={styles.taskCard}>
                <div style={styles.cardHeader}>
                  <div>
                    <h2 style={styles.taskTitle}>
                      {safe(item.task_title || item.title)}
                    </h2>

                    <p style={styles.taskMeta}>
                      {safe(item.seller_name)} - {safe(item.task_platform)}{" "}
                      {safe(item.task_type)}
                    </p>
                  </div>

                  <div style={styles.badgeArea}>
                    <span style={styles.ratingBadge}>
                      {getRatingFromTrust(item.seller_trust)} Star
                    </span>

                    <span
                      style={{
                        ...styles.riskBadge,
                        ...getRiskStyle(item.risk_level),
                      }}
                    >
                      {fraudProbability}% {safe(item.risk_level)} Risk
                    </span>
                  </div>
                </div>

                <div style={styles.middleGrid}>
                  <div>
                    <InfoLine
                      label="Trust Score"
                      value={Number(item.seller_trust || 0).toFixed(2)}
                    />

                    <InfoLine
                      label="Proof Status"
                      value={safe(item.proof_status || "pending")}
                    />

                    <InfoLine
                      label="Fraud Signals"
                      value={
                        signals.length > 0
                          ? `${signals.length} suspicious signal found`
                          : "No strong fraud signals"
                      }
                    />
                  </div>

                  <div>
                    <InfoLine
                      label="Submitted"
                      value={formatDate(item.analyzed_at || item.submitted_at)}
                    />

                    <InfoLine
                      label="Audit Status"
                      value={safe(item.audit_status || "not_checked")}
                    />

                    <InfoLine
                      label="Prediction"
                      value={safe(item.prediction)}
                    />
                  </div>
                </div>

                <div style={styles.probabilitySection}>
                  <div style={styles.probTop}>
                    <span>Fraud Probability</span>
                    <strong>{fraudProbability}%</strong>
                  </div>

                  <div style={styles.progressTrack}>
                    <div
                      style={{
                        ...styles.progressFill,
                        width: `${fraudProbability}%`,
                        background: getProbabilityColor(fraudProbability),
                      }}
                    ></div>
                  </div>
                </div>

                <div style={styles.quickSignalBox}>
                  {signals.length === 0 ? (
                    <span style={styles.safeSignal}>No strong fraud signals</span>
                  ) : (
                    signals.slice(0, 3).map((signal, index) => (
                      <span key={index} style={styles.signalChip}>
                        {signal.reason || signal.feature || "Suspicious signal"}
                      </span>
                    ))
                  )}
                </div>

                <div style={styles.actionRow}>
                  <button
                    style={styles.validBtn}
                    disabled={actionLoadingId === item.id}
                    onClick={() => handleAdminAction(item, "VALID_PROOF")}
                  >
                    ✓ Valid Proof
                  </button>

                  <button
                    style={styles.invalidBtn}
                    disabled={actionLoadingId === item.id}
                    onClick={() => handleAdminAction(item, "INVALID_PROOF")}
                  >
                    ✕ Invalid Proof
                  </button>

                  <button
                    style={styles.auditPassBtn}
                    disabled={actionLoadingId === item.id}
                    onClick={() => handleAdminAction(item, "AUDIT_PASSED")}
                  >
                    Audit Passed
                  </button>

                  <button
                    style={styles.auditFailBtn}
                    disabled={actionLoadingId === item.id}
                    onClick={() => handleAdminAction(item, "AUDIT_FAILED")}
                  >
                    Audit Failed
                  </button>

                  <button
                    style={styles.detailsBtn}
                    onClick={() => setOpenedCardId(isOpen ? null : item.id)}
                  >
                    {isOpen ? "Hide Details" : "View Fraud Details"}
                  </button>
                </div>

                {isOpen && (
                  <div style={styles.expandedArea}>
                    <div style={styles.expandedGrid}>
                      <DetailBox title="Seller Details">
                        <DetailRow label="Seller ID" value={item.seller_id} />
                        <DetailRow label="Seller Name" value={item.seller_name} />
                        <DetailRow label="Seller Type" value={item.seller_type} />
                        <DetailRow
                          label="Seller Age Days"
                          value={item.seller_age_days}
                        />
                        <DetailRow
                          label="Seller Trust Score"
                          value={item.seller_trust}
                        />
                      </DetailBox>

                      <DetailBox title="Task Details">
                        <DetailRow label="Task ID" value={item.task_id} />
                        <DetailRow label="Task Title" value={item.task_title} />
                        <DetailRow label="Platform" value={item.task_platform} />
                        <DetailRow label="Task Type" value={item.task_type} />
                        <DetailRow
                          label="Duplicate Screenshot"
                          value={item.is_duplicate_screenshot ? "Yes" : "No"}
                        />
                      </DetailBox>

                      <DetailBox title="Timing Check">
                        <DetailRow
                          label="Completion Duration"
                          value={item.completion_duration}
                        />
                        <DetailRow
                          label="Timing Risk Score"
                          value={item.timing_risk_score}
                        />
                        <DetailRow
                          label="Timing Classification"
                          value={item.timing_classification}
                        />
                        <DetailRow label="Z Score" value={item.z_score} />
                      </DetailBox>

                      <DetailBox title="Device / IP Check">
                        <DetailRow
                          label="Device Seller Count"
                          value={item.device_seller_count}
                        />
                        <DetailRow
                          label="Device Sharing Score"
                          value={item.device_sharing_score}
                        />
                        <DetailRow
                          label="IP Seller Count"
                          value={item.ip_seller_count}
                        />
                        <DetailRow
                          label="IP Reuse Score"
                          value={item.ip_reuse_score}
                        />
                      </DetailBox>
                    </div>

                    <div style={styles.signalPanel}>
                      <div style={styles.signalPanelHead}>
                        <h3 style={styles.panelTitle}>Suspicious Signals</h3>
                        <span style={styles.panelCount}>
                          {signals.length} signals
                        </span>
                      </div>

                      {signals.length === 0 ? (
                        <p style={styles.noData}>No suspicious signal found.</p>
                      ) : (
                        <div style={styles.signalList}>
                          {signals.map((signal, index) => (
                            <div key={index} style={styles.signalCard}>
                              <div style={styles.signalTop}>
                                <div>
                                  <h4 style={styles.signalReason}>
                                    {safe(signal.reason)}
                                  </h4>

                                  <p style={styles.signalLayer}>
                                    {safe(signal.layer)}
                                  </p>
                                </div>

                                <span style={styles.impactBadge}>
                                  Impact: {safe(signal.impact)}
                                </span>
                              </div>

                              <div style={styles.signalMetaGrid}>
                                <SmallData
                                  label="Feature"
                                  value={signal.feature}
                                />
                                <SmallData label="Value" value={signal.value} />
                                <SmallData label="Impact" value={signal.impact} />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    <div style={styles.reasonPanel}>
                      <h3 style={styles.panelTitle}>Fraud Reasons</h3>
                      <FraudReasons data={item.fraud_reasons} />
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function StatBox({ label, value, color }) {
  return (
    <div style={styles.statBox}>
      <p style={styles.statLabel}>{label}</p>
      <h2 style={{ ...styles.statValue, color }}>{value}</h2>
    </div>
  );
}

function InfoLine({ label, value }) {
  return (
    <p style={styles.infoLine}>
      <span>{label}:</span> <strong>{safe(value)}</strong>
    </p>
  );
}

function DetailBox({ title, children }) {
  return (
    <div style={styles.detailBox}>
      <h3 style={styles.detailTitle}>{title}</h3>
      {children}
    </div>
  );
}

function DetailRow({ label, value }) {
  return (
    <div style={styles.detailRow}>
      <span>{label}</span>
      <strong>{safe(value)}</strong>
    </div>
  );
}

function SmallData({ label, value }) {
  return (
    <div style={styles.smallData}>
      <span>{label}</span>
      <strong>{safe(value)}</strong>
    </div>
  );
}

function FraudReasons({ data }) {
  if (!data || data.length === 0) {
    return <p style={styles.noData}>No fraud reason found.</p>;
  }

  if (typeof data === "string") {
    return <p style={styles.reasonText}>{data}</p>;
  }

  if (Array.isArray(data)) {
    return (
      <div style={styles.reasonList}>
        {data.map((item, index) => {
          if (typeof item === "string") {
            return (
              <div key={index} style={styles.reasonItem}>
                {item}
              </div>
            );
          }

          if (typeof item === "object") {
            return (
              <div key={index} style={styles.reasonItem}>
                <strong>{item.reason || item.feature || "Fraud reason"}</strong>
                {item.layer && <p>Layer: {item.layer}</p>}
                {item.impact !== undefined && <p>Impact: {item.impact}</p>}
              </div>
            );
          }

          return (
            <div key={index} style={styles.reasonItem}>
              {String(item)}
            </div>
          );
        })}
      </div>
    );
  }

  if (typeof data === "object") {
    return (
      <pre style={styles.preBox}>
        {JSON.stringify(data, null, 2)}
      </pre>
    );
  }

  return <p style={styles.reasonText}>{String(data)}</p>;
}

function safe(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return value;
}

function formatDate(value) {
  if (!value) return "N/A";

  return new Date(value).toLocaleString("en-PK", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getProbabilityColor(value) {
  if (value >= 80) return "#dc2626";
  if (value >= 60) return "#ea580c";
  if (value >= 35) return "#d97706";
  return "#16a34a";
}

function getRiskStyle(risk) {
  if (risk === "LOW") {
    return {
      background: "#dcfce7",
      color: "#15803d",
      borderColor: "#86efac",
    };
  }

  if (risk === "MEDIUM") {
    return {
      background: "#fef3c7",
      color: "#b45309",
      borderColor: "#fcd34d",
    };
  }

  if (risk === "HIGH") {
    return {
      background: "#ffedd5",
      color: "#c2410c",
      borderColor: "#fdba74",
    };
  }

  if (risk === "CRITICAL") {
    return {
      background: "#fee2e2",
      color: "#dc2626",
      borderColor: "#fca5a5",
    };
  }

  return {
    background: "#f3f4f6",
    color: "#374151",
    borderColor: "#d1d5db",
  };
}

function getRatingFromTrust(score) {
  const value = Number(score || 0);

  if (value >= 90) return 5;
  if (value >= 70) return 4;
  if (value >= 45) return 3;
  if (value >= 25) return 2;
  return 1;
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#f8fafc",
    fontFamily: "Arial, sans-serif",
    color: "#0f172a",
  },

  topBar: {
    background: "linear-gradient(135deg, #047857, #10b981)",
    color: "white",
    padding: "26px 34px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "20px",
    borderBottomLeftRadius: "24px",
    borderBottomRightRadius: "24px",
  },

  title: {
    margin: 0,
    fontSize: "30px",
  },

  subtitle: {
    margin: "7px 0 0",
    color: "#ecfdf5",
  },

  refreshBtn: {
    background: "white",
    color: "#047857",
    border: "none",
    padding: "12px 18px",
    borderRadius: "12px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  errorBox: {
    margin: "22px 34px",
    background: "#fee2e2",
    color: "#dc2626",
    padding: "14px",
    borderRadius: "12px",
    fontWeight: "bold",
  },

  loadingBox: {
    margin: "22px 34px",
    background: "white",
    color: "#047857",
    padding: "14px",
    borderRadius: "12px",
    fontWeight: "bold",
  },

  statsGrid: {
    padding: "24px 34px 8px",
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
    gap: "14px",
  },

  statBox: {
    background: "white",
    padding: "18px",
    borderRadius: "16px",
    boxShadow: "0 8px 20px rgba(15,23,42,0.06)",
    border: "1px solid #e5e7eb",
  },

  statLabel: {
    color: "#64748b",
    margin: 0,
    fontWeight: "bold",
  },

  statValue: {
    margin: "8px 0 0",
    fontSize: "28px",
  },

  filterBar: {
    padding: "18px 34px",
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
  },

  filterBtn: {
    border: "1px solid #d1d5db",
    background: "white",
    color: "#334155",
    padding: "9px 14px",
    borderRadius: "999px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  activeFilterBtn: {
    background: "#047857",
    color: "white",
    borderColor: "#047857",
  },

  taskList: {
    padding: "0 34px 34px",
    display: "flex",
    flexDirection: "column",
    gap: "18px",
  },

  emptyBox: {
    background: "white",
    padding: "20px",
    borderRadius: "14px",
    color: "#64748b",
  },

  taskCard: {
    background: "white",
    border: "1px solid #e5e7eb",
    borderRadius: "18px",
    padding: "18px",
    boxShadow: "0 10px 25px rgba(15,23,42,0.06)",
  },

  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: "16px",
  },

  taskTitle: {
    margin: 0,
    fontSize: "20px",
    fontWeight: "600",
  },

  taskMeta: {
    margin: "6px 0 0",
    color: "#475569",
  },

  badgeArea: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    justifyContent: "flex-end",
  },

  ratingBadge: {
    background: "#fef3c7",
    color: "#b45309",
    padding: "6px 11px",
    borderRadius: "999px",
    fontSize: "13px",
    fontWeight: "bold",
  },

  riskBadge: {
    padding: "6px 11px",
    borderRadius: "999px",
    fontSize: "13px",
    fontWeight: "bold",
    border: "1px solid",
  },

  middleGrid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "20px",
    marginTop: "14px",
  },

  infoLine: {
    margin: "9px 0",
    color: "#334155",
  },

  probabilitySection: {
    marginTop: "14px",
  },

  probTop: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "14px",
    marginBottom: "7px",
    color: "#475569",
  },

  progressTrack: {
    height: "9px",
    background: "#e5e7eb",
    borderRadius: "999px",
    overflow: "hidden",
  },

  progressFill: {
    height: "100%",
    borderRadius: "999px",
  },

  quickSignalBox: {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    marginTop: "14px",
  },

  safeSignal: {
    border: "1px solid #e5e7eb",
    background: "white",
    color: "#111827",
    padding: "7px 10px",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "bold",
  },

  signalChip: {
    background: "#fff7ed",
    color: "#c2410c",
    border: "1px solid #fed7aa",
    padding: "7px 10px",
    borderRadius: "999px",
    fontSize: "13px",
    fontWeight: "bold",
  },

  actionRow: {
    display: "flex",
    gap: "10px",
    flexWrap: "wrap",
    marginTop: "16px",
  },

  validBtn: {
    background: "#16a34a",
    color: "white",
    border: "none",
    padding: "11px 18px",
    borderRadius: "999px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  invalidBtn: {
    background: "#e11d48",
    color: "white",
    border: "none",
    padding: "11px 18px",
    borderRadius: "999px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  auditPassBtn: {
    background: "white",
    color: "#111827",
    border: "1px solid #d1d5db",
    padding: "11px 18px",
    borderRadius: "999px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  auditFailBtn: {
    background: "white",
    color: "#dc2626",
    border: "1px solid #fecaca",
    padding: "11px 18px",
    borderRadius: "999px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  detailsBtn: {
    background: "#0f172a",
    color: "white",
    border: "none",
    padding: "11px 18px",
    borderRadius: "999px",
    fontWeight: "bold",
    cursor: "pointer",
  },

  expandedArea: {
    marginTop: "18px",
    paddingTop: "18px",
    borderTop: "1px solid #e5e7eb",
  },

  expandedGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: "14px",
  },

  detailBox: {
    background: "#f8fafc",
    border: "1px solid #e5e7eb",
    borderRadius: "14px",
    padding: "14px",
  },

  detailTitle: {
    margin: "0 0 10px",
    color: "#047857",
  },

  detailRow: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
    padding: "8px 0",
    borderBottom: "1px solid #e5e7eb",
    fontSize: "14px",
  },

  signalPanel: {
    background: "#f8fafc",
    border: "1px solid #e5e7eb",
    borderRadius: "14px",
    padding: "16px",
    marginTop: "14px",
  },

  signalPanelHead: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
    alignItems: "center",
    marginBottom: "12px",
  },

  panelTitle: {
    margin: 0,
    color: "#064e3b",
  },

  panelCount: {
    background: "#ecfdf5",
    color: "#047857",
    padding: "6px 10px",
    borderRadius: "999px",
    fontSize: "13px",
    fontWeight: "bold",
  },

  noData: {
    color: "#64748b",
    margin: 0,
  },

  signalList: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },

  signalCard: {
    background: "white",
    border: "1px solid #e5e7eb",
    borderRadius: "14px",
    padding: "14px",
  },

  signalTop: {
    display: "flex",
    justifyContent: "space-between",
    gap: "12px",
  },

  signalReason: {
    margin: 0,
    color: "#111827",
  },

  signalLayer: {
    margin: "5px 0 0",
    color: "#64748b",
    fontSize: "13px",
  },

  impactBadge: {
    background: "#fee2e2",
    color: "#dc2626",
    padding: "6px 10px",
    borderRadius: "999px",
    fontSize: "12px",
    fontWeight: "bold",
    height: "fit-content",
  },

  signalMetaGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
    gap: "10px",
    marginTop: "12px",
  },

  smallData: {
    background: "#f8fafc",
    padding: "10px",
    borderRadius: "10px",
    fontSize: "13px",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },

  reasonPanel: {
    background: "#fff7ed",
    border: "1px solid #fed7aa",
    borderRadius: "14px",
    padding: "16px",
    marginTop: "14px",
  },

  reasonText: {
    background: "white",
    padding: "12px",
    borderRadius: "12px",
    color: "#7c2d12",
    lineHeight: "1.6",
  },

  reasonList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },

  reasonItem: {
    background: "white",
    padding: "12px",
    borderRadius: "12px",
    color: "#7c2d12",
    lineHeight: "1.5",
  },

  preBox: {
    background: "#111827",
    color: "#d1fae5",
    padding: "12px",
    borderRadius: "12px",
    overflowX: "auto",
  },
};