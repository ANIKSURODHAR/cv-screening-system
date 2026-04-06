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

                  {/* ML Model Scores */}
                  <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>🧠 Individual Model Scores</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
                    {[
                      ["Logistic Regression", selectedApp.score.logistic_regression_score],
                      ["Naïve Bayes", selectedApp.score.naive_bayes_score],
                      ["KNN", selectedApp.score.knn_score],
                      ["Decision Tree", selectedApp.score.decision_tree_score],
                      ["Random Forest", selectedApp.score.random_forest_score],
                      ["SVM", selectedApp.score.svm_score],
                      ["XGBoost", selectedApp.score.xgboost_score],
                      ["AutoGluon", selectedApp.score.autogluon_score],
                    ].map(([name, score]) => (
                      <div key={name} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 11, color: C.dim, minWidth: 130 }}>{name}</span>
                        <Bar pct={score} color={score >= 80 ? C.green : score >= 60 ? C.amber : C.red} />
                        <span style={{ fontSize: 11, fontWeight: 700, color: score >= 80 ? C.green : score >= 60 ? C.amber : C.red }}>{score}%</span>
                      </div>
                    ))}
                  </div>

                  {/* SHAP Explanation */}
                  {selectedApp.score.shap_explanation && (
                    <div>
                      <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10 }}>💡 AI Explanation</h4>
                      {selectedApp.score.shap_explanation.summary && (
                        <div style={{ padding: 12, borderRadius: 8, background: `${C.accent}08`, border: `1px solid ${C.accent}20`, marginBottom: 12 }}>
                          <p style={{ fontSize: 12, color: C.dim, lineHeight: 1.7 }}>{selectedApp.score.shap_explanation.summary}</p>
                        </div>
                      )}
                      {selectedApp.score.shap_explanation.positive_factors?.length > 0 && (
                        <div style={{ marginBottom: 10 }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: C.green, marginBottom: 6 }}>✅ Positive Factors</div>
                          {selectedApp.score.shap_explanation.positive_factors.map((f, i) => (
                            <div key={i} style={{ fontSize: 12, color: C.dim, marginBottom: 4 }}>
                              • {f.factor} <span style={{ color: C.green }}>{f.impact}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {selectedApp.score.shap_explanation.improvement_suggestions?.length > 0 && (
                        <div style={{ padding: 12, borderRadius: 8, background: `${C.amber}08`, border: `1px solid ${C.amber}20` }}>
                          <div style={{ fontSize: 11, fontWeight: 600, color: C.amber, marginBottom: 6 }}>💡 Improvement Suggestions</div>
                          {selectedApp.score.shap_explanation.improvement_suggestions.map((s, i) => (
                            <div key={i} style={{ fontSize: 12, color: C.dim, marginBottom: 4 }}>→ {s}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
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
