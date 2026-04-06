import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: "", email: "", password: "", password_confirm: "",
    first_name: "", last_name: "", role: "candidate", company: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.password_confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await register(form);
      navigate("/login", { state: { message: "Registration successful! Please sign in." } });
    } catch (err) {
      const data = err.response?.data;
      const msg = data
        ? Object.values(data).flat().join(" ")
        : "Registration failed.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>⟐ CV.SCREEN</div>
        <h2 style={styles.title}>Create Account</h2>
        <p style={styles.subtitle}>Register as a recruiter or candidate</p>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          {/* Role Selection */}
          <div style={styles.field}>
            <label style={styles.label}>I am a</label>
            <div style={{ display: "flex", gap: 10 }}>
              {["candidate", "recruiter"].map((r) => (
                <button key={r} type="button" onClick={() => setForm({ ...form, role: r })}
                  style={{
                    ...styles.roleBtn,
                    background: form.role === r ? (r === "candidate" ? "rgba(16,185,129,0.15)" : "rgba(139,92,246,0.15)") : "#1a2235",
                    borderColor: form.role === r ? (r === "candidate" ? "#10b981" : "#8b5cf6") : "#1e2d4a",
                    color: form.role === r ? (r === "candidate" ? "#10b981" : "#8b5cf6") : "#64748b",
                  }}>
                  {r === "candidate" ? "🎯 Candidate" : "📋 Recruiter"}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={styles.field}>
              <label style={styles.label}>First Name</label>
              <input style={styles.input} name="first_name" value={form.first_name} onChange={handleChange} required />
            </div>
            <div style={styles.field}>
              <label style={styles.label}>Last Name</label>
              <input style={styles.input} name="last_name" value={form.last_name} onChange={handleChange} required />
            </div>
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Username</label>
            <input style={styles.input} name="username" value={form.username} onChange={handleChange} required />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Email</label>
            <input style={styles.input} name="email" type="email" value={form.email} onChange={handleChange} required />
          </div>

          {form.role === "recruiter" && (
            <div style={styles.field}>
              <label style={styles.label}>Company</label>
              <input style={styles.input} name="company" value={form.company} onChange={handleChange} placeholder="Your company name" />
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={styles.field}>
              <label style={styles.label}>Password</label>
              <input style={styles.input} name="password" type="password" value={form.password} onChange={handleChange} required />
            </div>
            <div style={styles.field}>
              <label style={styles.label}>Confirm</label>
              <input style={styles.input} name="password_confirm" type="password" value={form.password_confirm} onChange={handleChange} required />
            </div>
          </div>

          <button style={styles.button} type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        <p style={styles.footer}>
          Already have an account? <Link to="/login" style={styles.link}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
    background: "#0a0e17", fontFamily: "'Segoe UI', sans-serif",
  },
  card: {
    background: "#111827", border: "1px solid #1e2d4a", borderRadius: 16,
    padding: 36, width: 480, maxWidth: "92vw",
  },
  logo: { fontSize: 22, fontWeight: 700, color: "#3b82f6", letterSpacing: "0.05em", marginBottom: 20, textAlign: "center" },
  title: { fontSize: 22, fontWeight: 700, color: "#e2e8f0", marginBottom: 4, textAlign: "center" },
  subtitle: { fontSize: 13, color: "#64748b", marginBottom: 20, textAlign: "center" },
  field: { marginBottom: 14 },
  label: { display: "block", fontSize: 11, color: "#94a3b8", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.05em" },
  input: {
    width: "100%", padding: "10px 12px", borderRadius: 8, border: "1px solid #1e2d4a",
    background: "#1a2235", color: "#e2e8f0", fontSize: 13, outline: "none", boxSizing: "border-box",
  },
  roleBtn: {
    flex: 1, padding: "10px", borderRadius: 8, border: "1px solid #1e2d4a",
    cursor: "pointer", fontSize: 13, fontWeight: 600, background: "#1a2235",
  },
  button: {
    width: "100%", padding: "12px", borderRadius: 8, border: "none",
    background: "#3b82f6", color: "#fff", fontSize: 14, fontWeight: 600,
    cursor: "pointer", marginTop: 8,
  },
  error: {
    background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)",
    borderRadius: 8, padding: "10px 14px", color: "#ef4444", fontSize: 13, marginBottom: 14,
  },
  footer: { textAlign: "center", marginTop: 18, fontSize: 13, color: "#64748b" },
  link: { color: "#3b82f6", textDecoration: "none" },
};
