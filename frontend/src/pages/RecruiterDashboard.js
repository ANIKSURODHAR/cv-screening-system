import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { jobsAPI, candidatesAPI } from "../utils/api";

const C = { bg: "#0a0e17", surface: "#111827", surfaceAlt: "#1a2235", border: "#1e2d4a", accent: "#3b82f6", green: "#10b981", amber: "#f59e0b", red: "#ef4444", purple: "#8b5cf6", text: "#e2e8f0", dim: "#94a3b8", muted: "#64748b" };

const Badge = ({ label, color }) => (
  <span style={{ display: "inline-flex", padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600, background: `${color}18`, color, border: `1px solid ${color}30` }}>{label}</span>
);
const StatBox = ({ value, label, color }) => (
  <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 14, borderLeft: `3px solid ${color}` }}>
    <div style={{ fontSize: 26, fontWeight: 800, color }}>{value}</div>
    <div style={{ fontSize: 10, color: C.muted, textTransform: "uppercase", letterSpacing: "0.08em", marginTop: 4 }}>{label}</div>
  </div>
);
const Bar = ({ pct, color }) => (
  <div style={{ height: 5, borderRadius: 3, background: `${color}20`, width: "100%", position: "relative" }}>
    <div style={{ position: "absolute", top: 0, left: 0, height: "100%", width: `${Math.min(pct, 100)}%`, borderRadius: 3, background: color, transition: "width 0.8s" }} />
  </div>
);

export default function RecruiterDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("dashboard");
  const [myJobs, setMyJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applicants, setApplicants] = useState([]);
  const [jobForm, setJobForm] = useState({ title: "", company: user?.company || "", description: "", hard_requirements: "" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { loadMyJobs(); }, []);

  const loadMyJobs = async () => {
    try {
      const res = await jobsAPI.getMyJobs();
      setMyJobs(res.data.results || res.data);
    } catch (err) { console.error(err); }
  };

  const loadApplicants = async (jobId) => {
    try {
      const res = await candidatesAPI.getApplicants(jobId);
      setApplicants(res.data.results || res.data);
    } catch (err) { console.error(err); }
  };

  const handlePostJob = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMsg("");
    try {
      const reqs = jobForm.hard_requirements.split(",").filter(Boolean).map((r) => ({
        requirement_type: "skill",
        description: r.trim(),
        keywords: r.trim().toLowerCase(),
        is_mandatory: true,
      }));
      await jobsAPI.createJob({ ...jobForm, hard_requirements: reqs });
      setMsg("Job submitted for admin approval!");
      setJobForm({ title: "", company: user?.company || "", description: "", hard_requirements: "" });
      loadMyJobs();
    } catch (err) {
      setMsg("Error: " + (err.response?.data?.detail || JSON.stringify(err.response?.data)));
    } finally { setLoading(false); }
  };

  const handleStatusUpdate = async (appId, status) => {
    try {
      await candidatesAPI.updateStatus(appId, { status });
      loadApplicants(selectedJob.id);
    } catch (err) { alert("Failed to update status"); }
  };

  const s = {
    nav: (active) => ({ padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, background: active ? C.purple : "transparent", color: active ? "#fff" : C.dim }),
    card: { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 },
    tag: { display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, background: `${C.accent}15`, color: C.accent, marginRight: 6, marginBottom: 4 },
    input: { width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surfaceAlt, color: C.text, fontSize: 13, outline: "none", boxSizing: "border-box" },
    textarea: { width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${C.border}`, background: C.surfaceAlt, color: C.text, fontSize: 13, outline: "none", minHeight: 80, resize: "vertical", boxSizing: "border-box" },
    btn: (c) => ({ padding: "8px 18px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, background: c, color: "#fff" }),
    btnO: (c) => ({ padding: "5px 12px", borderRadius: 6, border: `1px solid ${c}`, cursor: "pointer", fontSize: 11, fontWeight: 600, background: "transparent", color: c }),
  };

  const totalApplicants = myJobs.reduce((a, j) => a + (j.applicant_count || 0), 0);

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 20px", borderBottom: `1px solid ${C.border}`, background: C.surface }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: C.accent }}>⟐ CV.SCREEN</span>
          <Badge label="Recruiter" color={C.purple} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, color: C.dim }}>{user?.first_name} · {user?.company}</span>
          <button onClick={logout} style={{ ...s.btn(C.red), padding: "6px 12px", fontSize: 11 }}>Logout</button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 4, padding: "14px 20px" }}>
        {[["dashboard", "Dashboard"], ["post-job", "Post Job"], ["applicants", "Applicants"]].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={s.nav(tab === key)}>{label}</button>
        ))}
      </div>

      <div style={{ padding: "0 20px 20px", maxHeight: "calc(100vh - 120px)", overflowY: "auto" }}>

        {tab === "dashboard" && (
          <div>
            <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 16 }}>📋 My Dashboard</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 20 }}>
              <StatBox value={myJobs.length} label="My Jobs" color={C.accent} />
              <StatBox value={totalApplicants} label="Total Applicants" color={C.green} />
              <StatBox value={myJobs.filter((j) => j.status === "pending").length} label="Pending Approval" color={C.amber} />
            </div>
            {myJobs.map((j) => (
              <div key={j.id} style={{ ...s.card, cursor: "pointer", background: C.surfaceAlt }} onClick={() => { setSelectedJob(j); loadApplicants(j.id); setTab("applicants"); }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontWeight: 700 }}>{j.title}</span>
                    <span style={{ margin: "0 8px" }}>—</span>
                    <Badge label={j.status?.toUpperCase()} color={j.status === "approved" ? C.green : j.status === "pending" ? C.amber : C.red} />
                  </div>
                  <span style={{ fontSize: 12, color: C.dim }}>{j.applicant_count || 0} applicants →</span>
                </div>
                <div style={{ marginTop: 8 }}>{j.hard_requirements?.map((r) => <span key={r.id} style={s.tag}>{r.description}</span>)}</div>
              </div>
            ))}
          </div>
        )}

        {tab === "post-job" && (
          <div style={s.card}>
            <h3 style={{ fontWeight: 700, marginBottom: 16 }}>Create New Job Posting</h3>
            {msg && <div style={{ padding: "10px 14px", borderRadius: 8, marginBottom: 14, background: msg.startsWith("Error") ? `${C.red}15` : `${C.green}15`, color: msg.startsWith("Error") ? C.red : C.green, fontSize: 13 }}>{msg}</div>}
            <form onSubmit={handlePostJob}>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                <div>
                  <label style={{ fontSize: 11, color: C.muted, display: "block", marginBottom: 4, textTransform: "uppercase" }}>Job Title</label>
                  <input style={s.input} value={jobForm.title} onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })} placeholder="e.g. Senior Data Scientist" required />
                </div>
                <div>
                  <label style={{ fontSize: 11, color: C.muted, display: "block", marginBottom: 4, textTransform: "uppercase" }}>Company</label>
                  <input style={s.input} value={jobForm.company} onChange={(e) => setJobForm({ ...jobForm, company: e.target.value })} required />
                </div>
                <div>
                  <label style={{ fontSize: 11, color: C.muted, display: "block", marginBottom: 4, textTransform: "uppercase" }}>Description</label>
                  <textarea style={s.textarea} value={jobForm.description} onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })} placeholder="Role, responsibilities..." required />
                </div>
                <div>
                  <label style={{ fontSize: 11, color: C.muted, display: "block", marginBottom: 4, textTransform: "uppercase" }}>Hard Requirements (comma separated)</label>
                  <input style={s.input} value={jobForm.hard_requirements} onChange={(e) => setJobForm({ ...jobForm, hard_requirements: e.target.value })} placeholder="e.g. Python 3+ yrs, TensorFlow, MSc required" required />
                  <div style={{ fontSize: 11, color: C.amber, marginTop: 4 }}>⚠ Candidates must pass ALL hard requirements before ML scoring</div>
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                  <button type="submit" disabled={loading} style={s.btn(C.accent)}>{loading ? "Submitting..." : "Submit for Admin Approval"}</button>
                </div>
                <div style={{ fontSize: 11, color: C.muted }}>ℹ Job goes live only after Admin approves it</div>
              </div>
            </form>
          </div>
        )}

        {tab === "applicants" && (
          <div>
            {selectedJob && (
              <div style={{ ...s.card, borderLeft: `3px solid ${C.accent}`, marginBottom: 14 }}>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{selectedJob.title}</div>
                <div style={{ fontSize: 12, color: C.muted, marginBottom: 8 }}>{selectedJob.description}</div>
                <div>{selectedJob.hard_requirements?.map((r) => <span key={r.id} style={s.tag}>{r.description}</span>)}</div>
              </div>
            )}
            <div style={s.card}>
              <h3 style={{ fontWeight: 700, marginBottom: 14 }}>Applicants — AI Ranked</h3>
              <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 13 }}>
                <thead><tr>{["#", "Candidate", "Hard", "ML", "Overall", "Status", "Action"].map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "10px 12px", color: C.muted, fontSize: 11, textTransform: "uppercase", borderBottom: `1px solid ${C.border}` }}>{h}</th>
                ))}</tr></thead>
                <tbody>
                  {applicants.map((a, i) => (
                    <tr key={a.id}>
                      <td style={{ padding: "10px 12px", fontWeight: 800, color: i === 0 ? C.green : C.muted }}>#{i + 1}</td>
                      <td style={{ padding: "10px 12px" }}><span style={{ fontWeight: 600 }}>{a.candidate_name}</span><br /><span style={{ fontSize: 11, color: C.muted }}>{a.candidate_email}</span></td>
                      <td style={{ padding: "10px 12px" }}><Bar pct={a.overall_score * 0.9} color={C.green} /></td>
                      <td style={{ padding: "10px 12px" }}><Bar pct={a.overall_score} color={C.accent} /></td>
                      <td style={{ padding: "10px 12px" }}>
                        {a.overall_score > 0
                          ? <Badge label={`${a.overall_score}% ${a.score_label}`} color={a.overall_score >= 80 ? C.green : a.overall_score >= 60 ? C.amber : C.red} />
                          : <Badge label="Processing" color={C.amber} />}
                      </td>
                      <td style={{ padding: "10px 12px" }}><Badge label={a.status?.toUpperCase()} color={a.status === "shortlisted" ? C.green : a.status === "rejected" ? C.red : C.accent} /></td>
                      <td style={{ padding: "10px 12px" }}>
                        <div style={{ display: "flex", gap: 4 }}>
                          <button onClick={() => handleStatusUpdate(a.id, "shortlisted")} style={s.btnO(C.green)}>Shortlist</button>
                          <button onClick={() => handleStatusUpdate(a.id, "rejected")} style={s.btnO(C.red)}>Reject</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {applicants.length === 0 && <div style={{ textAlign: "center", color: C.muted, padding: 30 }}>No applicants yet</div>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
