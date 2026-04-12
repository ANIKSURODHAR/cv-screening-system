import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { jobsAPI, candidatesAPI, mlAPI } from "../utils/api";

const C = { bg: "#0a0e17", surface: "#111827", surfaceAlt: "#1a2235", border: "#1e2d4a", accent: "#3b82f6", green: "#10b981", amber: "#f59e0b", red: "#ef4444", purple: "#8b5cf6", text: "#e2e8f0", dim: "#94a3b8", muted: "#64748b" };

const Badge = ({ label, color }) => (
  <span style={{ display: "inline-flex", padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${color}18`, color, border: `1px solid ${color}30` }}>{label}</span>
);

const ScoreBadge = ({ score }) => {
  const color = score >= 80 ? C.green : score >= 60 ? C.amber : C.red;
  const label = score >= 80 ? "High" : score >= 60 ? "Medium" : "Low";
  return <Badge label={`${score}% ${label}`} color={color} />;
};

const Bar = ({ pct, color }) => (
  <div style={{ height: 5, borderRadius: 3, background: `${color}20`, width: "100%", position: "relative" }}>
    <div style={{ position: "absolute", top: 0, left: 0, height: "100%", width: `${Math.min(pct, 100)}%`, borderRadius: 3, background: color, transition: "width 0.8s" }} />
  </div>
);

export default function CandidateDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("jobs");
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(null);
  const [cvFile, setCvFile] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifs, setShowNotifs] = useState(false);

  useEffect(() => {
    loadJobs();
    loadApplications();
    loadNotifications();
    // Poll for new notifications every 30 seconds
    const interval = setInterval(loadNotificationCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadNotifications = async () => {
    try {
      const res = await candidatesAPI.getNotifications();
      setNotifications(res.data.results || res.data);
      setUnreadCount((res.data.results || res.data).filter(n => !n.is_read).length);
    } catch (err) { console.error(err); }
  };

  const loadNotificationCount = async () => {
    try {
      const res = await candidatesAPI.unreadCount();
      setUnreadCount(res.data.count);
    } catch (err) { console.error(err); }
  };

  const markRead = async (id) => {
    try { await candidatesAPI.markRead(id); loadNotifications(); } catch (err) { console.error(err); }
  };

  const markAllRead = async () => {
    try { await candidatesAPI.markAllRead(); loadNotifications(); } catch (err) { console.error(err); }
  };
 

  useEffect(() => {
    loadJobs();
    loadApplications();
  }, []);

  const loadJobs = async () => {
    try {
      const res = await jobsAPI.getApprovedJobs();
      setJobs(res.data.results || res.data);
    } catch (err) { console.error(err); }
  };

  const loadApplications = async () => {
    try {
      const res = await candidatesAPI.getMyApplications();
      setApplications(res.data.results || res.data);
    } catch (err) { console.error(err); }
  };

  const handleApply = async (jobId) => {
    if (!cvFile) { alert("Please select a PDF file first"); return; }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("job", jobId);
      formData.append("cv_file", cvFile);
      await candidatesAPI.apply(formData);
      alert("Application submitted! AI scoring in progress...");
      setCvFile(null);
      setApplying(null);
      loadApplications();
    } catch (err) {
      alert(err.response?.data?.detail || JSON.stringify(err.response?.data) || "Failed to apply");
    } finally { setLoading(false); }
  };

  const loadAppDetail = async (appId) => {
    try {
      const res = await candidatesAPI.getMyApplicationDetail(appId);
      setSelectedApp(res.data);
      setTab("score-details");
    } catch (err) { console.error(err); }
  };

  const appliedJobIds = applications.map((a) => a.job?.id);

  const s = {
    nav: (active) => ({ padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, background: active ? C.accent : "transparent", color: active ? "#fff" : C.dim }),
    card: { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 },
    tag: { display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, background: `${C.accent}15`, color: C.accent, marginRight: 6, marginBottom: 4 },
    btn: (c) => ({ padding: "8px 18px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, background: c, color: "#fff" }),
  };

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 20px", borderBottom: `1px solid ${C.border}`, background: C.surface }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: C.accent }}>⟐ CV.SCREEN</span>
          <Badge label="Candidate" color={C.green} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, color: C.dim }}>Welcome, {user?.first_name}</span>
          {/* Notification Bell */}
          <div style={{ position: "relative" }}>
            <button onClick={() => { setShowNotifs(!showNotifs); if (!showNotifs) loadNotifications(); }}
              style={{ padding: "6px 10px", borderRadius: 8, border: `1px solid ${C.border}`, background: "transparent", color: C.dim, cursor: "pointer", fontSize: 16, position: "relative" }}>
              🔔
              {unreadCount > 0 && <span style={{ position: "absolute", top: -4, right: -4, width: 18, height: 18, borderRadius: "50%", background: C.red, color: "#fff", fontSize: 10, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center" }}>{unreadCount}</span>}
            </button>
            {showNotifs && (
              <div style={{ position: "absolute", top: "110%", right: 0, width: 360, maxHeight: 400, overflowY: "auto", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, zIndex: 100, boxShadow: "0 8px 30px rgba(0,0,0,0.4)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 14px", borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontSize: 13, fontWeight: 700 }}>Notifications</span>
                  {unreadCount > 0 && <button onClick={markAllRead} style={{ fontSize: 10, color: C.accent, background: "transparent", border: "none", cursor: "pointer" }}>Mark all read</button>}
                </div>
                {notifications.length === 0 ? (
                  <div style={{ padding: 30, textAlign: "center", color: C.muted, fontSize: 12 }}>No notifications yet</div>
                ) : notifications.map(n => (
                  <div key={n.id} onClick={() => markRead(n.id)} style={{ padding: "12px 14px", borderBottom: `1px solid ${C.border}08`, cursor: "pointer", background: n.is_read ? "transparent" : `${C.accent}05` }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 14 }}>{n.notification_type === "shortlisted" ? "🎉" : n.notification_type === "rejected" ? "📋" : n.notification_type === "hired" ? "🏆" : "ℹ️"}</span>
                      <span style={{ fontSize: 12, fontWeight: n.is_read ? 400 : 700, color: C.text }}>{n.title}</span>
                      {!n.is_read && <span style={{ width: 6, height: 6, borderRadius: "50%", background: C.accent }} />}
                    </div>
                    <div style={{ fontSize: 11, color: C.dim, lineHeight: 1.6, paddingLeft: 22 }}>{n.message}</div>
                    <div style={{ fontSize: 10, color: C.muted, paddingLeft: 22, marginTop: 4 }}>{new Date(n.created_at).toLocaleDateString()}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button onClick={logout} style={{ ...s.btn(C.red), padding: "6px 12px", fontSize: 11 }}>Logout</button>
        </div>
      </div>

      {/* Nav */}
      <div style={{ display: "flex", gap: 4, padding: "14px 20px" }}>
        {[["jobs", "Browse Jobs"], ["applications", "My Applications"], ["score-details", "Score Details"]].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={s.nav(tab === key)}>{label}</button>
        ))}
      </div>

      {/* Content */}
      <div style={{ padding: "0 20px 20px", maxHeight: "calc(100vh - 120px)", overflowY: "auto" }}>

        {/* Browse Jobs */}
        {tab === "jobs" && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>🎯 Browse Jobs</h2>
            <p style={{ fontSize: 12, color: C.dim, marginBottom: 18 }}>Apply to open positions with your CV</p>
            {jobs.map((j) => (
              <div key={j.id} style={{ ...s.card, borderLeft: `3px solid ${appliedJobIds.includes(j.id) ? C.green : C.accent}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{j.title}</div>
                    <div style={{ fontSize: 12, color: C.muted, marginBottom: 8 }}>{j.company} · {j.created_at?.slice(0, 10)}</div>
                    <p style={{ fontSize: 13, color: C.dim, marginBottom: 10 }}>{j.description}</p>
                    <div>{j.hard_requirements?.map((r) => <span key={r.id} style={s.tag}>{r.description}</span>)}</div>
                  </div>
                  <div style={{ textAlign: "right", minWidth: 130 }}>
                    {appliedJobIds.includes(j.id) ? (
                      <Badge label="APPLIED ✓" color={C.green} />
                    ) : applying === j.id ? (
                      <div>
                        <input type="file" accept=".pdf" onChange={(e) => setCvFile(e.target.files[0])} style={{ fontSize: 11, color: C.dim, marginBottom: 8, display: "block" }} />
                        <button onClick={() => handleApply(j.id)} disabled={loading} style={s.btn(C.green)}>
                          {loading ? "Uploading..." : "Submit CV"}
                        </button>
                      </div>
                    ) : (
                      <button onClick={() => setApplying(j.id)} style={s.btn(C.accent)}>📄 Apply</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {jobs.length === 0 && <div style={{ ...s.card, textAlign: "center", color: C.muted, padding: 40 }}>No open jobs available</div>}
          </div>
        )}

        {/* My Applications */}
        {tab === "applications" && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>📋 My Applications</h2>
            <p style={{ fontSize: 12, color: C.dim, marginBottom: 18 }}>Track your applications and AI scores</p>
            <div style={s.card}>
              <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 13 }}>
                <thead>
                  <tr>{["Job", "Company", "Score", "Status", "Applied", "Action"].map((h) => (
                    <th key={h} style={{ textAlign: "left", padding: "10px 12px", color: C.muted, fontSize: 11, textTransform: "uppercase", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                  ))}</tr>
                </thead>
                <tbody>
                  {applications.map((a) => (
                    <tr key={a.id}>
                      <td style={{ padding: "10px 12px", fontWeight: 600 }}>{a.job?.title}</td>
                      <td style={{ padding: "10px 12px", color: C.dim }}>{a.job?.company}</td>
                      <td style={{ padding: "10px 12px" }}>{a.overall_score > 0 ? <ScoreBadge score={a.overall_score} /> : <Badge label="Processing..." color={C.amber} />}</td>
                      <td style={{ padding: "10px 12px" }}><Badge label={a.status?.toUpperCase()} color={a.status === "shortlisted" ? C.green : a.status === "rejected" ? C.red : C.accent} /></td>
                      <td style={{ padding: "10px 12px", color: C.muted }}>{a.applied_at?.slice(0, 10)}</td>
                      <td style={{ padding: "10px 12px" }}>
                        <button onClick={() => loadAppDetail(a.id)} style={{ padding: "4px 10px", borderRadius: 4, border: `1px solid ${C.accent}`, background: "transparent", color: C.accent, cursor: "pointer", fontSize: 11 }}>View Details</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {applications.length === 0 && <div style={{ textAlign: "center", color: C.muted, padding: 30 }}>No applications yet</div>}
            </div>
          </div>
        )}

        {/* Score Details */}
        {tab === "score-details" && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>📊 Score Details</h2>
            <p style={{ fontSize: 12, color: C.dim, marginBottom: 18 }}>AI-powered analysis of your CV match</p>
            {selectedApp?.score ? (
              <div>
                <div style={{ ...s.card, borderLeft: `3px solid ${selectedApp.score.overall_score >= 80 ? C.green : selectedApp.score.overall_score >= 60 ? C.amber : C.red}` }}>
                  <h3 style={{ fontWeight: 700, marginBottom: 8 }}>{selectedApp.job?.title} — Score Breakdown</h3>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 16 }}>
                    <div style={{ background: C.surfaceAlt, borderRadius: 8, padding: 14, borderLeft: `3px solid ${C.green}` }}>
                      <div style={{ fontSize: 24, fontWeight: 800, color: C.green }}>{selectedApp.score.hard_req_score}%</div>
                      <div style={{ fontSize: 10, color: C.muted, textTransform: "uppercase" }}>Hard Requirements</div>
                    </div>
                    <div style={{ background: C.surfaceAlt, borderRadius: 8, padding: 14, borderLeft: `3px solid ${C.accent}` }}>
                      <div style={{ fontSize: 24, fontWeight: 800, color: C.accent }}>{selectedApp.score.ensemble_score}%</div>
                      <div style={{ fontSize: 10, color: C.muted, textTransform: "uppercase" }}>ML Ensemble</div>
                    </div>
                    <div style={{ background: C.surfaceAlt, borderRadius: 8, padding: 14, borderLeft: `3px solid ${C.purple}` }}>
                      <div style={{ fontSize: 24, fontWeight: 800, color: C.purple }}>{selectedApp.score.overall_score}%</div>
                      <div style={{ fontSize: 10, color: C.muted, textTransform: "uppercase" }}>Overall</div>
                    </div>
                  </div>

                  {/* ML Model Scores with Explanations */}
                  <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>🧠 Individual Model Scores — How Each Model Decided</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: 10, marginBottom: 16 }}>
                    {[
                      {
                        name: "Logistic Regression",
                        score: selectedApp.score.logistic_regression_score,
                        weight: "10%",
                        icon: "📐",
                        why: "Baseline model — simple, fast, and interpretable",
                        how: "Assigns a weight to each of the 384 BERT features. If the combined weighted sum is above a threshold, predicts 'good match'. Uses sigmoid function to convert to probability.",
                        decided: function(s) {
                          if (s >= 80) return "High positive weights on your skill-related features pushed the score above the match threshold.";
                          if (s >= 60) return "Some skill features had positive weights, but others were near zero — moderate confidence in match.";
                          return "The weighted combination of your CV features fell below the match threshold — key job-related features had low or negative weights.";
                        },
                        strength: "Very fast prediction. Clear feature importance — you can see exactly which features mattered most.",
                      },
                      {
                        name: "Naive Bayes",
                        score: selectedApp.score.naive_bayes_score,
                        weight: "10%",
                        icon: "🎲",
                        why: "Probabilistic classifier — calculates match probability using Bayes' theorem",
                        how: "For each BERT feature, estimates the probability distribution for 'match' vs 'no match'. Multiplies all probabilities together (naive independence assumption) to get final P(match|CV).",
                        decided: function(s) {
                          if (s >= 80) return "The probability distributions of your CV features closely match the 'good match' training examples.";
                          if (s >= 60) return "Some feature distributions match, but others overlap between match/no-match classes.";
                          return "Your CV feature distributions look more like 'not match' training examples than 'good match' ones.";
                        },
                        strength: "Extremely fast. Works well even with limited training data. Naturally outputs calibrated probabilities.",
                      },
                      {
                        name: "KNN (K-Nearest Neighbors)",
                        score: selectedApp.score.knn_score,
                        weight: "10%",
                        icon: "📍",
                        why: "Instance-based — finds the 7 most similar CVs from training data",
                        how: "Converts your CV to 384 BERT numbers, then finds the 7 closest training CVs using cosine distance. If 5 of 7 nearest neighbors were 'good match', predicts good match.",
                        decided: function(s) {
                          if (s >= 80) return "Most of the 7 nearest training CVs (by BERT similarity) were good matches — your CV is very similar to successful candidates.";
                          if (s >= 60) return "The 7 nearest neighbors were mixed — some good matches, some not. Your CV sits in a borderline zone.";
                          return "Most of the 7 nearest training CVs were NOT good matches — your CV's BERT representation is far from typical good-match CVs.";
                        },
                        strength: "No assumptions about data distribution. Adapts to complex decision boundaries. Great for finding 'similar candidates'.",
                      },
                      {
                        name: "Random Forest",
                        score: selectedApp.score.random_forest_score,
                        weight: "20%",
                        icon: "🌲",
                        why: "Ensemble of 200 decision trees — reduces overfitting through voting",
                        how: "Creates 200 different decision trees, each trained on a random subset of data and features. Each tree votes 'match' or 'no match'. Final answer = majority vote. This randomness prevents memorizing noise.",
                        decided: function(s) {
                          if (s >= 80) return "Strong majority of the 200 trees voted 'good match' — your CV features consistently triggered match-positive branches across many different tree structures.";
                          if (s >= 60) return "Trees were split — roughly 60% voted match. Some feature combinations triggered match, others didn't.";
                          return "Most trees voted 'not match' — your CV features consistently fell into no-match branches across different tree structures.";
                        },
                        strength: "Very robust — hard to overfit. Built-in feature importance. Good balance of accuracy and reliability.",
                      },
                      {
                        name: "SVM (Support Vector Machine)",
                        score: selectedApp.score.svm_score,
                        weight: "15%",
                        icon: "🔲",
                        why: "Finds the optimal boundary between match and no-match in high-dimensional space",
                        how: "Uses RBF kernel to map your 384 BERT features into an even higher-dimensional space. Finds the hyperplane that maximizes the gap between match and no-match CVs. Only CVs near the boundary (support vectors) affect the decision.",
                        decided: function(s) {
                          if (s >= 80) return "Your CV sits clearly on the 'good match' side of the decision boundary — far from the separator.";
                          if (s >= 60) return "Your CV is near the decision boundary — some features push toward match, others toward no-match.";
                          return "Your CV is on the 'no match' side of the decision boundary in the high-dimensional feature space.";
                        },
                        strength: "Excellent with high-dimensional BERT features. Memory efficient — only stores support vectors. Handles complex non-linear patterns.",
                      },
                      {
                        name: "XGBoost",
                        score: selectedApp.score.xgboost_score,
                        weight: "35%",
                        icon: "🚀",
                        why: "Best performer — gradient boosting where each tree corrects previous errors",
                        how: "Trains 300 trees sequentially. Tree 1 makes initial prediction. Tree 2 focuses on samples Tree 1 got wrong. Tree 3 fixes what Trees 1+2 missed. After 300 rounds, the combined prediction is highly refined. Uses regularization to prevent overfitting.",
                        decided: function(s) {
                          if (s >= 80) return "After 300 rounds of error correction, the ensemble confidently predicts 'good match' — your CV features survived multiple rounds of scrutiny.";
                          if (s >= 60) return "The boosted ensemble gives moderate confidence — early trees predicted match, but later correction trees introduced uncertainty.";
                          return "The boosting process converged on 'not match' — even after 300 rounds of correction, your CV features didn't meet the match threshold.";
                        },
                        strength: "Highest accuracy among all models. Handles missing values. Built-in regularization prevents overfitting. Gets the highest ensemble weight (35%).",
                      },
                    ].map((m) => {
                      const sc = m.score || 0;
                      const col = sc >= 80 ? C.green : sc >= 60 ? C.amber : C.red;
                      return (
                        <div key={m.name} style={{ background: C.surfaceAlt, borderRadius: 10, padding: 14, border: `1px solid ${C.border}` }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <span style={{ fontSize: 18 }}>{m.icon}</span>
                              <div>
                                <span style={{ fontSize: 13, fontWeight: 700, color: C.text }}>{m.name}</span>
                                <span style={{ fontSize: 10, color: C.muted, marginLeft: 8 }}>Weight: {m.weight}</span>
                              </div>
                            </div>
                            <span style={{ fontSize: 18, fontWeight: 800, color: col }}>{sc}%</span>
                          </div>
                          <Bar pct={sc} color={col} />
                          <div style={{ marginTop: 10, fontSize: 11, lineHeight: 1.8, color: C.dim }}>
                            <div style={{ marginBottom: 4 }}><span style={{ color: C.accent, fontWeight: 600 }}>WHY THIS MODEL:</span> {m.why}</div>
                            <div style={{ marginBottom: 4 }}><span style={{ color: C.purple, fontWeight: 600 }}>HOW IT WORKS:</span> {m.how}</div>
                            <div style={{ padding: 8, borderRadius: 6, background: `${col}10`, border: `1px solid ${col}25`, marginTop: 6 }}>
                              <span style={{ color: col, fontWeight: 600 }}>DECISION:</span> {m.decided(sc)}
                            </div>
                          </div>
                          <div style={{ marginTop: 6, fontSize: 10, color: C.muted, fontStyle: "italic" }}>Strength: {m.strength}</div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Score Formula Explanation */}
                  <div style={{ background: C.surfaceAlt, borderRadius: 10, padding: 14, border: `1px solid ${C.border}`, marginBottom: 16 }}>
                    <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>📐 How the {selectedApp.score.overall_score}% Overall Score Was Calculated</h4>
                    <div style={{ fontSize: 12, color: C.dim, lineHeight: 2 }}>
                      <div style={{ padding: 10, borderRadius: 6, background: `${C.bg}`, marginBottom: 8, fontFamily: "monospace", fontSize: 11 }}>
                        {selectedApp.score.hard_req_passed ? (
                          <div>
                            <div style={{ color: C.green }}>✓ Hard requirements PASSED → full formula applies:</div>
                            <div style={{ marginTop: 4 }}>Overall = (30% × Hard Req) + (70% × ML Ensemble)</div>
                            <div style={{ marginTop: 2 }}>Overall = (0.3 × {selectedApp.score.hard_req_score}%) + (0.7 × {selectedApp.score.ensemble_score}%)</div>
                            <div style={{ marginTop: 2, color: C.accent, fontWeight: 700 }}>Overall = {selectedApp.score.overall_score}%</div>
                          </div>
                        ) : (
                          <div>
                            <div style={{ color: C.red }}>✗ Hard requirements FAILED → score capped at 50%:</div>
                            <div style={{ marginTop: 4 }}>Overall = (50% × Hard Req) + (50% × ML Ensemble), capped at 50%</div>
                            <div style={{ marginTop: 2 }}>Overall = (0.5 × {selectedApp.score.hard_req_score}%) + (0.5 × {selectedApp.score.ensemble_score}%)</div>
                            <div style={{ marginTop: 2, color: C.red, fontWeight: 700 }}>Overall = {selectedApp.score.overall_score}% (capped because hard reqs failed)</div>
                          </div>
                        )}
                      </div>
                      <div style={{ marginTop: 6 }}>
                        <span style={{ fontWeight: 600, color: C.text }}>ML Ensemble Score ({selectedApp.score.ensemble_score}%):</span>
                        <span> Weighted average of all model scores. XGBoost counts 35%, Random Forest 20%, SVM 15%, others 10% each.</span>
                      </div>
                    </div>
                  </div>

                  {/* SHAP Explanation — Selected Because / Rejected Because */}
                  {selectedApp.score.shap_explanation && (() => {
                    const shap = selectedApp.score.shap_explanation;
                    const selected = shap.selected_because || shap.positive_factors || [];
                    const rejected = shap.rejected_because || shap.negative_factors || [];
                    const suggestions = shap.improvement_suggestions || [];
                    return (
                    <div>
                      <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>🔍 Why Your CV Got This Score</h4>

                      {/* Summary */}
                      {shap.summary && (
                        <div style={{ padding: 12, borderRadius: 8, background: `${C.accent}08`, border: `1px solid ${C.accent}20`, marginBottom: 12 }}>
                          <p style={{ fontSize: 12, color: C.dim, lineHeight: 1.7 }}>{shap.summary}</p>
                        </div>
                      )}

                      {/* Selected Because */}
                      {selected.length > 0 && (
                        <div style={{ padding: 12, borderRadius: 8, background: `${C.green}08`, border: `1px solid ${C.green}20`, marginBottom: 10 }}>
                          <div style={{ fontSize: 12, fontWeight: 700, color: C.green, marginBottom: 8 }}>✅ Selected Because (points gained):</div>
                          {selected.map((f, i) => (
                            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "start", fontSize: 12, color: C.dim, marginBottom: 6, paddingLeft: 8, borderLeft: `2px solid ${C.green}30` }}>
                              <div>
                                <div style={{ fontWeight: 600 }}>{f.factor}</div>
                                {f.type && <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>Category: {f.type}</div>}
                                {f.details && f.details.map((d, j) => <div key={j} style={{ fontSize: 10, color: C.muted }}>  {d}</div>)}
                              </div>
                              <span style={{ color: C.green, fontWeight: 700, minWidth: 50, textAlign: "right" }}>{f.impact}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Rejected Because */}
                      {rejected.length > 0 && (
                        <div style={{ padding: 12, borderRadius: 8, background: `${C.red}08`, border: `1px solid ${C.red}20`, marginBottom: 10 }}>
                          <div style={{ fontSize: 12, fontWeight: 700, color: C.red, marginBottom: 8 }}>❌ Rejected Because (points lost):</div>
                          {rejected.map((f, i) => (
                            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "start", fontSize: 12, color: C.dim, marginBottom: 6, paddingLeft: 8, borderLeft: `2px solid ${C.red}30` }}>
                              <div>
                                <div style={{ fontWeight: 600 }}>{f.factor}</div>
                                {f.mandatory && <span style={{ fontSize: 10, color: C.red, fontWeight: 600 }}> (MANDATORY)</span>}
                                {f.type && <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>Category: {f.type}</div>}
                              </div>
                              <span style={{ color: C.red, fontWeight: 700, minWidth: 50, textAlign: "right" }}>{f.impact}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Bias Mitigation Info */}
                      {shap.bias_info && (
                        <div style={{ padding: 10, borderRadius: 8, background: `${C.purple}08`, border: `1px solid ${C.purple}20`, marginBottom: 10 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: C.purple, marginBottom: 4 }}>🛡️ Bias Mitigation Applied</div>
                          <div style={{ fontSize: 11, color: C.dim }}>{shap.bias_info.message}</div>
                          {shap.bias_info.items_removed?.length > 0 && shap.bias_info.items_removed.map((item, i) => (
                            <div key={i} style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>• {item}</div>
                          ))}
                        </div>
                      )}

                      {/* Improvement Suggestions */}
                      {suggestions.length > 0 && (
                        <div style={{ padding: 12, borderRadius: 8, background: `${C.amber}08`, border: `1px solid ${C.amber}20` }}>
                          <div style={{ fontSize: 12, fontWeight: 700, color: C.amber, marginBottom: 8 }}>💡 How to Improve Your Score:</div>
                          {suggestions.map((sug, i) => (
                            <div key={i} style={{ fontSize: 12, color: C.dim, marginBottom: 4, paddingLeft: 8 }}>→ {sug}</div>
                          ))}
                        </div>
                      )}
                    </div>
                    );
                  })()}
                </div>
              </div>
            ) : (
              <div style={{ ...s.card, textAlign: "center", color: C.muted, padding: 40 }}>
                Select an application from "My Applications" tab to view score details
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
