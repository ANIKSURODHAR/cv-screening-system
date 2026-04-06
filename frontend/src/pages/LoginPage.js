import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login(username, password);
      // Redirect based on role
      if (user.role === "admin" || user.is_superuser) navigate("/admin");
      else if (user.role === "recruiter") navigate("/recruiter");
      else navigate("/candidate");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>⟐ CV.SCREEN</div>
        <h2 style={styles.title}>Sign In</h2>
        <p style={styles.subtitle}>Enter your credentials to continue</p>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div style={styles.field}>
            <label style={styles.label}>Username</label>
            <input
              style={styles.input}
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
            />
          </div>
          <div style={styles.field}>
            <label style={styles.label}>Password</label>
            <input
              style={styles.input}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>
          <button style={styles.button} type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p style={styles.footer}>
          Don't have an account?{" "}
          <Link to="/register" style={styles.link}>Register here</Link>
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
    padding: 40, width: 400, maxWidth: "90vw",
  },
  logo: { fontSize: 22, fontWeight: 700, color: "#3b82f6", letterSpacing: "0.05em", marginBottom: 24, textAlign: "center" },
  title: { fontSize: 24, fontWeight: 700, color: "#e2e8f0", marginBottom: 4, textAlign: "center" },
  subtitle: { fontSize: 14, color: "#64748b", marginBottom: 24, textAlign: "center" },
  field: { marginBottom: 16 },
  label: { display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" },
  input: {
    width: "100%", padding: "12px 14px", borderRadius: 8, border: "1px solid #1e2d4a",
    background: "#1a2235", color: "#e2e8f0", fontSize: 14, outline: "none", boxSizing: "border-box",
  },
  button: {
    width: "100%", padding: "12px", borderRadius: 8, border: "none",
    background: "#3b82f6", color: "#fff", fontSize: 14, fontWeight: 600,
    cursor: "pointer", marginTop: 8,
  },
  error: {
    background: "rgba(239,68,68,0.12)", border: "1px solid rgba(239,68,68,0.3)",
    borderRadius: 8, padding: "10px 14px", color: "#ef4444", fontSize: 13, marginBottom: 16,
  },
  footer: { textAlign: "center", marginTop: 20, fontSize: 13, color: "#64748b" },
  link: { color: "#3b82f6", textDecoration: "none" },
};
