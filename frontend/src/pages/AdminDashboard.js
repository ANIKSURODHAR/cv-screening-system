import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { authAPI, jobsAPI, candidatesAPI } from "../utils/api";

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

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("overview");
  const [stats, setStats] = useState({});
  const [allJobs, setAllJobs] = useState([]);
  const [pendingJobs, setPendingJobs] = useState([]);
  const [recruiters, setRecruiters] = useState([]);
  const [candidates, setCandidates] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, jobsRes, pendingRes, usersRes] = await Promise.all([
        authAPI.getStats(),
        jobsAPI.getAllJobs(),
        jobsAPI.getPendingJobs(),
        authAPI.getUsers(),
      ]);
      setStats(statsRes.data);
      setAllJobs(jobsRes.data.results || jobsRes.data);
      setPendingJobs(pendingRes.data.results || pendingRes.data);
      const users = usersRes.data.results || usersRes.data;
      setRecruiters(users.filter((u) => u.role === "recruiter"));
      setCandidates(users.filter((u) => u.role === "candidate"));
    } catch (err) { console.error(err); }
  };

  const handleApprove = async (jobId) => {
    try {
      await jobsAPI.approveJob(jobId, { status: "approved" });
      loadData();
    } catch (err) { alert("Failed to approve job"); }
  };

  const handleReject = async (jobId) => {
    try {
      await jobsAPI.approveJob(jobId, { status: "rejected" });
      loadData();
    } catch (err) { alert("Failed to reject job"); }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to remove this user?")) return;
    try {
      await authAPI.deleteUser(userId);
      loadData();
    } catch (err) { alert("Failed to delete user"); }
  };

  const s = {
    nav: (active) => ({ padding: "8px 16px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, background: active ? C.red : "transparent", color: active ? "#fff" : C.dim }),
    card: { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 18, marginBottom: 14 },
    tag: { display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 600, background: `${C.accent}15`, color: C.accent, marginRight: 6, marginBottom: 4 },
    btn: (c) => ({ padding: "8px 18px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, background: c, color: "#fff" }),
    btnO: (c) => ({ padding: "5px 12px", borderRadius: 6, border: `1px solid ${c}`, cursor: "pointer", fontSize: 11, fontWeight: 600, background: "transparent", color: c }),
    th: { textAlign: "left", padding: "10px 12px", color: C.muted, fontSize: 11, textTransform: "uppercase", borderBottom: `1px solid ${C.border}` },
    td: { padding: "10px 12px", borderBottom: `1px solid ${C.border}08` },
  };

  return (
    <div style={{ background: C.bg, minHeight: "100vh", color: C.text }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 20px", borderBottom: `1px solid ${C.border}`, background: C.surface }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: C.accent }}>⟐ CV.SCREEN</span>
          <Badge label="Admin" color={C.red} />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ fontSize: 13, color: C.dim }}>Admin: {user?.first_name}</span>
          <button onClick={logout} style={{ ...s.btn(C.red), padding: "6px 12px", fontSize: 11 }}>Logout</button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 4, padding: "14px 20px" }}>
        {[["overview", "Overview"], ["pending", "Pending Jobs"], ["recruiters", "Recruiters"], ["candidates", "Candidates"]].map(([key, label]) => (
          <button key={key} onClick={() => setTab(key)} style={s.nav(tab === key)}>{label}</button>
        ))}
      </div>

      <div style={{ padding: "0 20px 20px", maxHeight: "calc(100vh - 120px)", overflowY: "auto" }}>
        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14, marginBottom: 20 }}>
          <StatBox value={stats.total_jobs || 0} label="Total Jobs" color={C.accent} />
          <StatBox value={stats.pending_jobs || 0} label="Pending" color={C.amber} />
          <StatBox value={stats.candidates || 0} label="Candidates" color={C.green} />
          <StatBox value={stats.recruiters || 0} label="Recruiters" color={C.purple} />
        </div>

        {/* Overview — All Jobs */}
        {tab === "overview" && (
          <div style={s.card}>
            <h3 style={{ fontWeight: 700, marginBottom: 14 }}>All Jobs</h3>
            <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 13 }}>
              <thead><tr>{["Job", "Recruiter", "Status", "Applicants", "Posted"].map((h) => <th key={h} style={s.th}>{h}</th>)}</tr></thead>
              <tbody>
                {allJobs.map((j) => (
                  <tr key={j.id}>
                    <td style={s.td}><span style={{ fontWeight: 600 }}>{j.title}</span><br /><span style={{ fontSize: 11, color: C.muted }}>{j.company}</span></td>
                    <td style={s.td}>{j.recruiter_name}</td>
                    <td style={s.td}><Badge label={j.status?.toUpperCase()} color={j.status === "approved" ? C.green : j.status === "pending" ? C.amber : C.red} /></td>
                    <td style={s.td}>{j.applicant_count || 0}</td>
                    <td style={s.td}><span style={{ color: C.muted }}>{j.created_at?.slice(0, 10)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pending Jobs */}
        {tab === "pending" && (
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 14 }}>⏳ Jobs Awaiting Approval</h3>
            {pendingJobs.length === 0 ? (
              <div style={{ ...s.card, textAlign: "center", color: C.muted, padding: 40 }}>✅ No pending jobs</div>
            ) : pendingJobs.map((j) => (
              <div key={j.id} style={{ ...s.card, borderLeft: `3px solid ${C.amber}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 16 }}>{j.title}</div>
                    <div style={{ fontSize: 12, color: C.muted }}>{j.company} — by {j.recruiter_name}</div>
                    <p style={{ fontSize: 13, color: C.dim, margin: "10px 0" }}>{j.description}</p>
                    <div>{j.hard_requirements?.map((r) => <span key={r.id} style={s.tag}>{r.description}</span>)}</div>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button onClick={() => handleApprove(j.id)} style={s.btn(C.green)}>✓ Approve</button>
                    <button onClick={() => handleReject(j.id)} style={s.btn(C.red)}>✗ Reject</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Recruiters */}
        {tab === "recruiters" && (
          <div style={s.card}>
            <h3 style={{ fontWeight: 700, marginBottom: 14 }}>Registered Recruiters</h3>
            <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 13 }}>
              <thead><tr>{["Name", "Email", "Company", "Joined", "Actions"].map((h) => <th key={h} style={s.th}>{h}</th>)}</tr></thead>
              <tbody>
                {recruiters.map((r) => (
                  <tr key={r.id}>
                    <td style={s.td}><span style={{ fontWeight: 600 }}>{r.first_name} {r.last_name}</span></td>
                    <td style={s.td}><span style={{ color: C.muted }}>{r.email}</span></td>
                    <td style={s.td}>{r.company}</td>
                    <td style={s.td}><span style={{ color: C.muted }}>{r.created_at?.slice(0, 10)}</span></td>
                    <td style={s.td}><button onClick={() => handleDeleteUser(r.id)} style={s.btnO(C.red)}>Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Candidates */}
        {tab === "candidates" && (
          <div style={s.card}>
            <h3 style={{ fontWeight: 700, marginBottom: 14 }}>Registered Candidates</h3>
            <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: 0, fontSize: 13 }}>
              <thead><tr>{["Name", "Email", "Joined", "Actions"].map((h) => <th key={h} style={s.th}>{h}</th>)}</tr></thead>
              <tbody>
                {candidates.map((c) => (
                  <tr key={c.id}>
                    <td style={s.td}><span style={{ fontWeight: 600 }}>{c.first_name} {c.last_name}</span></td>
                    <td style={s.td}><span style={{ color: C.muted }}>{c.email}</span></td>
                    <td style={s.td}><span style={{ color: C.muted }}>{c.created_at?.slice(0, 10)}</span></td>
                    <td style={s.td}><button onClick={() => handleDeleteUser(c.id)} style={s.btnO(C.red)}>Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
