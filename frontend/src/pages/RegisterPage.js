import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authAPI } from "../utils/api";

const P = {
  cream: "#f8f5f0", warmWhite: "#faf8f5", gold: "#d4a843", goldLight: "#e8d5a0",
  goldBg: "linear-gradient(145deg, #f5ecd7, #faf6ed)", dark: "#1a1a1a", dimText: "#6b6b6b",
  inputBg: "#f2efe8", inputBorder: "#e0dcd4", accent: "#c9a227",
};

export default function RegisterPage() {
  const [form, setForm] = useState({
  username:"",
  email:"",
  password:"",
  password_confirm:"",
  first_name:"",
  last_name:"",
  role:"candidate"
});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault(); setError("");
    if (form.password !== form.password_confirm) { setError("Passwords do not match"); return; }
    setLoading(true);
    try {
      await authAPI.register(form);
      navigate("/login");
    } catch (err) {
      const data = err.response?.data;
      if (typeof data === "object") {
        const msgs = Object.values(data).flat().join(", ");
        setError(msgs);
      } else { setError("Registration failed"); }
    } finally { setLoading(false); }
  };

  const upd = (k, v) => setForm({ ...form, [k]: v });

  return (
    <div style={{ display:"flex", minHeight:"100vh", fontFamily:"'DM Sans', 'Segoe UI', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
        * { margin:0; padding:0; box-sizing:border-box; }
        input::placeholder,select { color:#b0a898; }
        input:focus,select:focus { outline:none; border-color:${P.gold} !important; box-shadow:0 0 0 3px ${P.gold}20; }
        @keyframes fadeIn { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
        @keyframes float { 0%,100% { transform:translateY(0); } 50% { transform:translateY(-8px); } }
      `}</style>

      {/* Left: Register Form */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", justifyContent:"center", padding:"40px 80px", background:P.warmWhite, position:"relative", overflowY:"auto" }}>
        <div style={{ position:"absolute", top:40, left:80 }}>
          <span style={{ fontSize:18, fontWeight:700, color:P.dark, fontFamily:"'Playfair Display',serif", padding:"8px 20px", border:`1.5px solid ${P.dark}20`, borderRadius:30 }}>CV.SCREEN</span>
        </div>

        <div style={{ maxWidth:420, width:"100%", animation:"fadeIn 0.6s ease", marginTop:60 }}>
          <h1 style={{ fontSize:30, fontWeight:700, color:P.dark, fontFamily:"'Playfair Display',serif", marginBottom:8 }}>Create an account</h1>
          <p style={{ fontSize:14, color:P.dimText, marginBottom:28 }}>Join CV.SCREEN to find your perfect match</p>

          {error && <div style={{ padding:"12px 16px", borderRadius:12, background:"#fef2f2", border:"1px solid #fecaca", color:"#dc2626", fontSize:13, marginBottom:16 }}>{error}</div>}

          <form onSubmit={handleSubmit}>
            <div style={{ display:"flex", gap:12, marginBottom:16 }}>
              <div style={{ flex:1 }}>
                <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>First name</label>
                <input value={form.first_name} onChange={e => upd("first_name", e.target.value)} placeholder="Anik" required
                  style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" }} />
              </div>
              <div style={{ flex:1 }}>
                <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>Last name</label>
                <input value={form.last_name} onChange={e => upd("last_name", e.target.value)} placeholder="Sutrodhar" required
                  style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" }} />
              </div>
            </div>

            <div style={{ marginBottom:16 }}>
              <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>Username</label>
              <input value={form.username} onChange={e => upd("username", e.target.value)} placeholder="anik_dev" required
                style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" }} />
            </div>

            <div style={{ marginBottom:16 }}>
              <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>Email</label>
              <input value={form.email} onChange={e => upd("email", e.target.value)} placeholder="anik@email.com" type="email" required
                style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" }} />
            </div>

            <div style={{ marginBottom:16 }}>
              <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>I am a</label>
              <select value={form.role} onChange={e => upd("role", e.target.value)}
                style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'", cursor:"pointer", appearance:"auto" }}>
                <option value="candidate">Candidate — looking for jobs</option>
                <option value="recruiter">Recruiter — hiring talent</option>
              </select>
            </div>

            <div style={{ display:"flex", gap:12, marginBottom:24 }}>
              <div style={{ flex:1 }}>
                <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>Password</label>
                <input value={form.password} onChange={e => upd("password", e.target.value)} placeholder="••••••••" type="password" required
                  style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" }} />
              </div>
              <div style={{ flex:1 }}>
                <label style={{ display:"block", fontSize:12, color:P.dimText, marginBottom:6 }}>Confirm</label>

                <input value={form.password_confirm} onChange={e => upd("password_confirm", e.target.value)} placeholder="••••••••" type="password" required
                  style={{ width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.inputBorder}`, background:P.inputBg, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" }} />
              </div>
            </div>

            <button type="submit" disabled={loading}
              style={{ width:"100%", padding:"14px", borderRadius:14, border:"none", background:P.goldBg, color:P.dark, fontSize:15, fontWeight:600, fontFamily:"'DM Sans'", cursor:"pointer", boxShadow:"0 4px 20px rgba(212,168,67,0.15)", opacity:loading?0.7:1 }}>
              {loading ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p style={{ textAlign:"center", marginTop:24, fontSize:13, color:P.dimText }}>
            Already have an account? <Link to="/login" style={{ color:P.accent, textDecoration:"none", fontWeight:600 }}>Sign in</Link>
          </p>
        </div>
      </div>

      {/* Right: Visual Panel */}
      <div style={{ flex:1, background:"linear-gradient(135deg, #f5ecd7 0%, #e8d5a0 50%, #d4c089 100%)", display:"flex", alignItems:"center", justifyContent:"center", position:"relative", overflow:"hidden" }}>
        <div style={{ position:"absolute", top:-50, right:-50, width:200, height:200, borderRadius:"50%", background:"rgba(255,255,255,0.15)" }} />
        <div style={{ position:"absolute", bottom:-30, left:-30, width:150, height:150, borderRadius:"50%", background:"rgba(255,255,255,0.1)" }} />

        <div style={{ position:"relative", zIndex:1, textAlign:"center", maxWidth:420, padding:40 }}>
          <div style={{ animation:"float 4s ease-in-out infinite" }}>
            <div style={{ background:"rgba(255,255,255,0.95)", borderRadius:16, padding:"14px 22px", display:"inline-block", marginBottom:20, boxShadow:"0 8px 30px rgba(0,0,0,0.08)" }}>
              <div style={{ fontSize:14, fontWeight:700, color:P.dark }}>Join 9,544+ professionals</div>
              <div style={{ fontSize:11, color:P.dimText, marginTop:2 }}>AI-powered career matching</div>
            </div>
          </div>

          <div style={{ background:"rgba(255,255,255,0.85)", borderRadius:16, padding:24, textAlign:"left", boxShadow:"0 8px 30px rgba(0,0,0,0.06)" }}>
            <div style={{ fontSize:18, fontWeight:700, color:P.dark, fontFamily:"'Playfair Display',serif", marginBottom:16 }}>How it works</div>
            {[
              ["1", "Upload your CV", "PDF format, AI extracts your skills"],
              ["2", "AI scores your match", "6 models analyze your fit"],
              ["3", "Get detailed feedback", "Know exactly what to improve"],
            ].map(([num, title, desc]) => (
              <div key={num} style={{ display:"flex", gap:12, marginBottom:14 }}>
                <div style={{ width:32, height:32, borderRadius:10, background:P.goldBg, display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, fontWeight:700, color:P.dark, flexShrink:0 }}>{num}</div>
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
