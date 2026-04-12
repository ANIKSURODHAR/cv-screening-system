import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const P = {
  cream: "#f8f5f0", warmWhite: "#faf8f5", gold: "#d4a843", goldLight: "#e8d5a0",
  goldBg: "linear-gradient(145deg, #f5ecd7, #faf6ed)", dark: "#1a1a1a", dimText: "#6b6b6b",
  inputBg: "#f2efe8", inputBorder: "#e0dcd4", accent: "#c9a227",
};

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const user = await login(username, password);
      if (user.role === "admin" || user.is_superuser) navigate("/admin");
      else if (user.role === "recruiter") navigate("/recruiter");
      else navigate("/candidate");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Check your credentials.");
    } finally { setLoading(false); }
  };

  return (
    <div style={{ display:"flex", minHeight:"100vh", fontFamily:"'DM Sans', 'Segoe UI', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
        * { margin:0; padding:0; box-sizing:border-box; }
        input::placeholder { color:#b0a898; }
        input:focus { outline:none; border-color:${P.gold} !important; box-shadow:0 0 0 3px ${P.gold}20; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
        @keyframes float { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-8px); } }
      `}</style>

      {/* ═══ Left: Login Form ═══ */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", justifyContent:"center", padding:"60px 80px", background:P.warmWhite, position:"relative", minHeight:"100vh" }}>
        {/* Logo */}
        <div style={{ position:"absolute", top:40, left:80 }}>
          <span style={{ fontSize:18, fontWeight:700, color:P.dark, fontFamily:"'Playfair Display',serif", padding:"8px 20px", border:`1.5px solid ${P.dark}20`, borderRadius:30 }}>CV.SCREEN</span>
        </div>

        <div style={{ maxWidth:400, width:"100%", animation:"fadeIn 0.6s ease" }}>
          <h1 style={{ fontSize:32, fontWeight:700, color:P.dark, fontFamily:"'Playfair Display',serif", marginBottom:8 }}>Welcome back</h1>
          <p style={{ fontSize:14, color:P.dimText, marginBottom:36 }}>Sign in to your account to continue</p>

          {error && (
            <div style={{ padding:"12px 16px", borderRadius:12, background:"#fef2f2", border:"1px solid #fecaca", color:"#dc2626", fontSize:13, marginBottom:20 }}>{error}</div>
          )}

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom:20 }}>
              <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:8, letterSpacing:"0.03em" }}>Username</label>
              <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Enter your username" required
                style={{ width:"100%", padding:"14px 18px", borderRadius:14, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:15, fontFamily:"'DM Sans'" }} />
            </div>

            <div style={{ marginBottom:28 }}>
              <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:8, letterSpacing:"0.03em" }}>Password</label>
              <div style={{ position:"relative" }}>
                <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Enter your password" required
                  type={showPass ? "text" : "password"}
                  style={{ width:"100%", padding:"14px 50px 14px 18px", borderRadius:14, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:15, fontFamily:"'DM Sans'" }} />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  style={{ position:"absolute", right:14, top:"50%", transform:"translateY(-50%)", background:"none", border:"none", cursor:"pointer", fontSize:16, color:P.dimText }}>
                  {showPass ? "◡" : "⊙"}
                </button>
              </div>
            </div>

            <button type="submit" disabled={loading}
              style={{ width:"100%", padding:"15px", borderRadius:14, border:"none", background:P.goldBg, color:P.dark, fontSize:15, fontWeight:600, fontFamily:"'DM Sans'", cursor:"pointer", transition:"all 0.3s", boxShadow:"0 4px 20px rgba(212,168,67,0.15)", opacity:loading?0.7:1 }}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          <div style={{ display:"flex", alignItems:"center", gap:12, margin:"24px 0" }}>
            <div style={{ flex:1, height:1, background:P.inputBorder }} />
            <span style={{ fontSize:12, color:P.dimText }}>or continue with</span>
            <div style={{ flex:1, height:1, background:P.inputBorder }} />
          </div>

          <div style={{ display:"flex", gap:12 }}>
            <button style={{ flex:1, padding:"12px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:"transparent", cursor:"pointer", fontSize:13, fontFamily:"'DM Sans'", color:P.dark, display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
              <span style={{ fontSize:16 }}>🍎</span> Apple
            </button>
            <button style={{ flex:1, padding:"12px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:"transparent", cursor:"pointer", fontSize:13, fontFamily:"'DM Sans'", color:P.dark, display:"flex", alignItems:"center", justifyContent:"center", gap:8 }}>
              <span style={{ fontSize:16 }}>🔵</span> Google
            </button>
          </div>

          <div style={{ display:"flex", justifyContent:"space-between", marginTop:32 }}>
            <p style={{ fontSize:13, color:P.dimText }}>Don't have an account? <Link to="/register" style={{ color:P.accent, textDecoration:"none", fontWeight:600 }}>Sign up</Link></p>
            <Link to="/register" style={{ fontSize:13, color:P.dimText, textDecoration:"none" }}>Terms & Conditions</Link>
          </div>
        </div>
      </div>

      {/* ═══ Right: Visual Panel ═══ */}
      <div style={{ flex:1, background:"linear-gradient(135deg, #f5ecd7 0%, #e8d5a0 50%, #d4c089 100%)", display:"flex", alignItems:"center", justifyContent:"center", position:"relative", overflow:"hidden", minHeight:"100vh" }}>
        {/* Decorative circles */}
        <div style={{ position:"absolute", top:-50, right:-50, width:200, height:200, borderRadius:"50%", background:"rgba(255,255,255,0.15)" }} />
        <div style={{ position:"absolute", bottom:-30, left:-30, width:150, height:150, borderRadius:"50%", background:"rgba(255,255,255,0.1)" }} />

        {/* Content Card */}
        <div style={{ position:"relative", zIndex:1, textAlign:"center", maxWidth:420, padding:40 }}>
          {/* Floating cards */}
          <div style={{ animation:"float 4s ease-in-out infinite" }}>
            <div style={{ background:"rgba(255,255,255,0.95)", borderRadius:16, padding:"14px 22px", display:"inline-block", marginBottom:16, boxShadow:"0 8px 30px rgba(0,0,0,0.08)" }}>
              <div style={{ fontSize:13, fontWeight:700, color:P.dark }}>AI-Powered CV Screening</div>
              <div style={{ fontSize:11, color:P.dimText, marginTop:2 }}>Smart matching with 6 ML models</div>
            </div>
          </div>

          {/* Stats */}
          <div style={{ display:"flex", gap:12, justifyContent:"center", marginBottom:24 }}>
            {[["9,544+", "CVs Analyzed"], ["6", "AI Models"], ["79%+", "Accuracy"]].map(([val, label]) => (
              <div key={label} style={{ background:"rgba(255,255,255,0.9)", borderRadius:14, padding:"16px 20px", boxShadow:"0 4px 16px rgba(0,0,0,0.05)", minWidth:90 }}>
                <div style={{ fontSize:20, fontWeight:800, color:P.dark, fontFamily:"'DM Sans'" }}>{val}</div>
                <div style={{ fontSize:10, color:P.dimText, marginTop:2 }}>{label}</div>
              </div>
            ))}
          </div>

          {/* Feature list */}
          <div style={{ background:"rgba(255,255,255,0.85)", borderRadius:16, padding:20, textAlign:"left", boxShadow:"0 8px 30px rgba(0,0,0,0.06)" }}>
            {[
              ["BERT deep understanding", "Semantic CV-job matching"],
              ["Bias-free scoring", "Name, gender, age removed"],
              ["SHAP explanations", "See why you scored high/low"],
            ].map(([title, desc]) => (
              <div key={title} style={{ display:"flex", alignItems:"center", gap:12, padding:"8px 0", borderBottom:"1px solid rgba(0,0,0,0.04)" }}>
                <div style={{ width:28, height:28, borderRadius:8, background:P.goldBg, display:"flex", alignItems:"center", justifyContent:"center", fontSize:12 }}>✓</div>
                <div>
                  <div style={{ fontSize:13, fontWeight:600, color:P.dark }}>{title}</div>
                  <div style={{ fontSize:11, color:P.dimText }}>{desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
