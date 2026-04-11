import React, { useState, useEffect, useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import { jobsAPI, candidatesAPI, mlAPI } from "../utils/api";

const C = {
  bg: "#060a13", surface: "#0d1321", surfaceAlt: "#131b2e", surfaceHover: "#182240",
  border: "#1c2a4a", borderLight: "#243358",
  accent: "#4f8ff7", accentDark: "#2d6be0",
  green: "#0dd99e", amber: "#f7b731", red: "#f25c54", purple: "#9b72f2", cyan: "#22d3ee",
  text: "#edf2f7", dim: "#94a3b8", muted: "#5e6e85",
  glass: "rgba(13,19,33,0.85)",
};

const GlobalStyle = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    * { margin:0; padding:0; box-sizing:border-box; }
    ::-webkit-scrollbar { width:4px; }
    ::-webkit-scrollbar-track { background:${C.bg}; }
    ::-webkit-scrollbar-thumb { background:${C.border}; border-radius:4px; }
    ::selection { background:${C.accent}40; color:#fff; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(12px); } to { opacity:1; transform:translateY(0); } }
    @keyframes glow { 0%,100% { box-shadow:0 0 15px rgba(79,143,247,0.1); } 50% { box-shadow:0 0 25px rgba(79,143,247,0.2); } }
    .card-hover:hover { border-color:${C.borderLight} !important; transform:translateY(-1px); }
    .card-hover { transition:all 0.25s cubic-bezier(0.4,0,0.2,1); }
    input:focus,select:focus { outline:none; border-color:${C.accent} !important; box-shadow:0 0 0 3px ${C.accent}15; }
  `}</style>
);

const Badge = ({ label, color }) => (
  <span style={{ display:"inline-flex", alignItems:"center", gap:4, padding:"4px 12px", borderRadius:20, fontSize:11, fontWeight:600, fontFamily:"'DM Sans'", background:`${color}12`, color, border:`1px solid ${color}25`, letterSpacing:"0.02em" }}>{label}</span>
);
const ScoreBadge = ({ score }) => { const c = score >= 80 ? C.green : score >= 60 ? C.amber : C.red; return <Badge label={`${score}% ${score >= 80 ? "High" : score >= 60 ? "Medium" : "Low"}`} color={c} />; };
const Bar = ({ pct, color, height = 6 }) => (
  <div style={{ height, borderRadius:height, background:`${color}15`, width:"100%", position:"relative", overflow:"hidden" }}>
    <div style={{ position:"absolute", top:0, left:0, height:"100%", width:`${Math.min(pct,100)}%`, borderRadius:height, background:`linear-gradient(90deg,${color}90,${color})`, transition:"width 1s cubic-bezier(0.4,0,0.2,1)" }} />
  </div>
);
const GlassCard = ({ children, style = {}, hover, glow, ...p }) => (
  <div className={hover ? "card-hover" : ""} style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:16, padding:20, backdropFilter:"blur(12px)", ...(glow ? { animation:"glow 3s ease-in-out infinite" } : {}), ...style }} {...p}>{children}</div>
);
const StatCard = ({ value, label, color, icon }) => (
  <div style={{ background:C.surfaceAlt, borderRadius:12, padding:16, borderLeft:`3px solid ${color}`, position:"relative", overflow:"hidden" }}>
    <div style={{ position:"absolute", top:10, right:14, fontSize:22, opacity:0.15 }}>{icon}</div>
    <div style={{ fontSize:28, fontWeight:800, color, letterSpacing:"-0.03em", fontFamily:"'DM Sans'" }}>{value}</div>
    <div style={{ fontSize:10, color:C.muted, textTransform:"uppercase", letterSpacing:"0.08em", marginTop:4 }}>{label}</div>
  </div>
);
const parseSalary = (r) => { if (!r) return { min:0, max:0, display:"" }; const n = r.match(/[\d,]+/g); if (!n) return { min:0, max:0, display:r }; const p = n.map(x => parseInt(x.replace(/,/g,""))); return { min:p[0]||0, max:p[1]||p[0]||0, display:r }; };

export default function CandidateDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("jobs");
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(null);
  const [cvFile, setCvFile] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [salaryMin, setSalaryMin] = useState("");
  const [salaryMax, setSalaryMax] = useState("");
  const [expandedModel, setExpandedModel] = useState(null);

  useEffect(() => { loadJobs(); loadApplications(); }, []);
  const loadJobs = async () => { try { const r = await jobsAPI.getApprovedJobs(); setJobs(r.data.results || r.data); } catch(e) { console.error(e); } };
  const loadApplications = async () => { try { const r = await candidatesAPI.getMyApplications(); setApplications(r.data.results || r.data); } catch(e) { console.error(e); } };
  const handleApply = async (jobId) => {
    if (!cvFile) { alert("Please select a PDF file first"); return; }
    setLoading(true);
    try { const f = new FormData(); f.append("job", jobId); f.append("cv_file", cvFile); await candidatesAPI.apply(f); alert("Application submitted! AI scoring in progress..."); setCvFile(null); setApplying(null); loadApplications(); }
    catch (e) { alert(e.response?.data?.detail || JSON.stringify(e.response?.data) || "Failed"); }
    finally { setLoading(false); }
  };
  const loadAppDetail = async (id) => { try { const r = await candidatesAPI.getMyApplicationDetail(id); setSelectedApp(r.data); setTab("score-details"); } catch(e) { console.error(e); } };
  const appliedJobIds = applications.map(a => a.job?.id);

  const filteredJobs = useMemo(() => jobs.filter(j => {
    const q = searchQuery.toLowerCase();
    const ms = !q || j.title?.toLowerCase().includes(q) || j.company?.toLowerCase().includes(q) || j.description?.toLowerCase().includes(q) || j.hard_requirements?.some(r => r.description?.toLowerCase().includes(q));
    const sal = parseSalary(j.salary_range);
    const mMin = !salaryMin || sal.max >= parseInt(salaryMin);
    const mMax = !salaryMax || sal.min <= parseInt(salaryMax);
    return ms && mMin && mMax;
  }), [jobs, searchQuery, salaryMin, salaryMax]);

  const tabs = [{ key:"jobs", label:"Browse Jobs", icon:"◎" }, { key:"applications", label:"My Applications", icon:"◫" }, { key:"score-details", label:"Score Details", icon:"◈" }];

  return (
    <div style={{ background:C.bg, minHeight:"100vh", color:C.text, fontFamily:"'DM Sans',sans-serif" }}>
      <GlobalStyle />

      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"16px 24px", borderBottom:`1px solid ${C.border}`, background:C.glass, backdropFilter:"blur(20px)", position:"sticky", top:0, zIndex:10 }}>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <div style={{ width:32, height:32, borderRadius:8, background:`linear-gradient(135deg,${C.accent},${C.purple})`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:14, fontWeight:800, color:"#fff" }}>CV</div>
            <span style={{ fontSize:18, fontWeight:800, letterSpacing:"-0.02em" }}>CV.SCREEN</span>
          </div>
          <Badge label="Candidate" color={C.green} />
        </div>
        <div style={{ display:"flex", alignItems:"center", gap:14 }}>
          <div style={{ textAlign:"right" }}>
            <div style={{ fontSize:13, fontWeight:600 }}>{user?.first_name} {user?.last_name}</div>
            <div style={{ fontSize:10, color:C.muted }}>{user?.email}</div>
          </div>
          <button onClick={logout} style={{ padding:"7px 16px", borderRadius:8, border:`1px solid ${C.red}30`, cursor:"pointer", fontSize:11, fontWeight:600, fontFamily:"'DM Sans'", background:`${C.red}10`, color:C.red }}>Logout</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display:"flex", gap:4, padding:"16px 24px 0" }}>
        {tabs.map(({ key, label, icon }) => (
          <button key={key} onClick={() => setTab(key)} style={{ padding:"10px 20px", borderRadius:"10px 10px 0 0", border:"none", cursor:"pointer", fontSize:13, fontWeight:600, fontFamily:"'DM Sans'", background:tab===key?C.surface:"transparent", color:tab===key?C.accent:C.muted, borderBottom:tab===key?`2px solid ${C.accent}`:"2px solid transparent", transition:"all 0.2s" }}>
            <span style={{ marginRight:6, opacity:0.6 }}>{icon}</span>{label}
          </button>
        ))}
      </div>

      <div style={{ padding:"20px 24px", maxHeight:"calc(100vh - 130px)", overflowY:"auto" }}>

        {/* ═══ BROWSE JOBS ═══ */}
        {tab === "jobs" && (
          <div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12, marginBottom:20 }}>
              <StatCard value={jobs.length} label="Open Positions" color={C.accent} icon="◎" />
              <StatCard value={applications.length} label="My Applications" color={C.green} icon="◫" />
              <StatCard value={applications.filter(a => a.status === "shortlisted").length} label="Shortlisted" color={C.purple} icon="★" />
            </div>

            {/* Search + Salary Filter */}
            <GlassCard style={{ padding:14, marginBottom:16, display:"flex", alignItems:"center", gap:12, flexWrap:"wrap" }}>
              <div style={{ position:"relative", flex:1, minWidth:200 }}>
                <span style={{ position:"absolute", left:14, top:"50%", transform:"translateY(-50%)", fontSize:14, color:C.muted }}>⌕</span>
                <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search jobs by title, company, or skills..."
                  style={{ width:"100%", padding:"10px 14px 10px 38px", borderRadius:10, border:`1px solid ${C.border}`, background:C.surfaceAlt, color:C.text, fontSize:13, fontFamily:"'DM Sans'" }} />
              </div>
              <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                <span style={{ fontSize:11, color:C.muted, whiteSpace:"nowrap" }}>💰 Salary:</span>
                <input value={salaryMin} onChange={e => setSalaryMin(e.target.value)} placeholder="Min" type="number"
                  style={{ width:80, padding:"8px", borderRadius:8, border:`1px solid ${C.border}`, background:C.surfaceAlt, color:C.text, fontSize:12, fontFamily:"'DM Sans'" }} />
                <span style={{ color:C.muted }}>–</span>
                <input value={salaryMax} onChange={e => setSalaryMax(e.target.value)} placeholder="Max" type="number"
                  style={{ width:80, padding:"8px", borderRadius:8, border:`1px solid ${C.border}`, background:C.surfaceAlt, color:C.text, fontSize:12, fontFamily:"'DM Sans'" }} />
              </div>
              {(searchQuery || salaryMin || salaryMax) && (
                <button onClick={() => { setSearchQuery(""); setSalaryMin(""); setSalaryMax(""); }}
                  style={{ padding:"8px 14px", borderRadius:8, border:`1px solid ${C.border}`, background:"transparent", color:C.muted, cursor:"pointer", fontSize:11, fontFamily:"'DM Sans'" }}>Clear</button>
              )}
              <span style={{ fontSize:11, color:C.muted, marginLeft:"auto" }}>{filteredJobs.length} of {jobs.length} jobs</span>
            </GlassCard>

            {/* Job Cards */}
            {filteredJobs.map((j, idx) => {
              const sal = parseSalary(j.salary_range);
              const applied = appliedJobIds.includes(j.id);
              return (
                <GlassCard key={j.id} hover style={{ marginBottom:12, borderLeft:`3px solid ${applied?C.green:C.accent}`, animation:`fadeUp 0.3s ease ${idx*0.05}s both` }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"start", gap:16 }}>
                    <div style={{ flex:1 }}>
                      <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:6 }}>
                        <span style={{ fontSize:17, fontWeight:700 }}>{j.title}</span>
                        {j.job_type && <Badge label={j.job_type} color={C.cyan} />}
                      </div>
                      <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:10 }}>
                        <span style={{ fontSize:12, color:C.dim }}>⧫ {j.company}</span>
                        <span style={{ fontSize:12, color:C.muted }}>· {j.created_at?.slice(0,10)}</span>
                        {sal.display && <span style={{ fontSize:12, color:C.green, fontWeight:600 }}>💰 {sal.display}</span>}
                      </div>
                      <p style={{ fontSize:13, color:C.dim, marginBottom:12, lineHeight:1.7, maxHeight:52, overflow:"hidden" }}>{j.description}</p>
                      <div style={{ display:"flex", flexWrap:"wrap", gap:4 }}>
                        {j.hard_requirements?.map(r => <span key={r.id} style={{ display:"inline-block", padding:"3px 10px", borderRadius:6, fontSize:10, fontWeight:600, background:`${C.accent}10`, color:C.accent, border:`1px solid ${C.accent}18` }}>{r.description}</span>)}
                      </div>
                    </div>
                    <div style={{ textAlign:"right", minWidth:140 }}>
                      {applied ? (
                        <div><Badge label="APPLIED ✓" color={C.green} />
                          {(() => { const a = applications.find(a => a.job?.id === j.id); return a?.overall_score > 0 ? <div style={{ marginTop:8 }}><ScoreBadge score={a.overall_score} /></div> : null; })()}
                        </div>
                      ) : applying === j.id ? (
                        <div>
                          <label style={{ display:"block", padding:"10px 14px", borderRadius:8, border:`1px dashed ${C.accent}40`, background:`${C.accent}05`, cursor:"pointer", fontSize:11, color:C.accent, textAlign:"center", marginBottom:8 }}>
                            {cvFile ? cvFile.name.slice(0,20) : "Choose PDF"}<input type="file" accept=".pdf" onChange={e => setCvFile(e.target.files[0])} style={{ display:"none" }} />
                          </label>
                          <div style={{ display:"flex", gap:6 }}>
                            <button onClick={() => handleApply(j.id)} disabled={loading||!cvFile} style={{ flex:1, padding:"8px 14px", borderRadius:8, border:"none", cursor:"pointer", fontSize:11, fontWeight:700, fontFamily:"'DM Sans'", background:cvFile?C.green:C.muted, color:"#fff", opacity:loading?0.6:1 }}>{loading ? "Scoring..." : "Submit"}</button>
                            <button onClick={() => { setApplying(null); setCvFile(null); }} style={{ padding:"8px 10px", borderRadius:8, border:`1px solid ${C.border}`, background:"transparent", color:C.muted, cursor:"pointer", fontSize:10 }}>✕</button>
                          </div>
                        </div>
                      ) : (
                        <button onClick={() => setApplying(j.id)} style={{ padding:"10px 22px", borderRadius:10, border:"none", cursor:"pointer", fontSize:12, fontWeight:700, fontFamily:"'DM Sans'", background:`linear-gradient(135deg,${C.accent},${C.accentDark})`, color:"#fff", boxShadow:`0 4px 15px ${C.accent}25` }}>Apply Now</button>
                      )}
                    </div>
                  </div>
                </GlassCard>
              );
            })}
            {filteredJobs.length === 0 && (
              <GlassCard style={{ textAlign:"center", padding:50 }}>
                <div style={{ fontSize:36, marginBottom:12, opacity:0.3 }}>◎</div>
                <div style={{ color:C.muted, fontSize:14 }}>{searchQuery||salaryMin||salaryMax ? "No jobs match your filters" : "No open positions"}</div>
                {(searchQuery||salaryMin||salaryMax) && <button onClick={() => { setSearchQuery(""); setSalaryMin(""); setSalaryMax(""); }} style={{ marginTop:12, padding:"8px 20px", borderRadius:8, border:`1px solid ${C.accent}30`, background:"transparent", color:C.accent, cursor:"pointer", fontSize:12, fontFamily:"'DM Sans'" }}>Clear filters</button>}
              </GlassCard>
            )}
          </div>
        )}

        {/* ═══ MY APPLICATIONS ═══ */}
        {tab === "applications" && (
          <div>
            <h2 style={{ fontSize:20, fontWeight:700, marginBottom:16, letterSpacing:"-0.02em" }}>My Applications</h2>
            <GlassCard style={{ padding:0, overflow:"hidden" }}>
              <table style={{ width:"100%", borderCollapse:"separate", borderSpacing:0, fontSize:13 }}>
                <thead><tr>{["Job","Company","Score","Status","Applied","Action"].map(h => <th key={h} style={{ textAlign:"left", padding:"14px 16px", color:C.muted, fontSize:10, textTransform:"uppercase", letterSpacing:"0.08em", borderBottom:`1px solid ${C.border}`, background:C.surfaceAlt, fontFamily:"'DM Sans'" }}>{h}</th>)}</tr></thead>
                <tbody>{applications.map(a => (
                  <tr key={a.id} style={{ transition:"background 0.15s" }} onMouseEnter={e => e.currentTarget.style.background=C.surfaceHover} onMouseLeave={e => e.currentTarget.style.background="transparent"}>
                    <td style={{ padding:"14px 16px", fontWeight:600 }}>{a.job?.title}</td>
                    <td style={{ padding:"14px 16px", color:C.dim }}>{a.job?.company}</td>
                    <td style={{ padding:"14px 16px" }}>{a.overall_score > 0 ? <ScoreBadge score={a.overall_score} /> : <Badge label="Processing..." color={C.amber} />}</td>
                    <td style={{ padding:"14px 16px" }}><Badge label={a.status?.toUpperCase()} color={a.status==="shortlisted"?C.green:a.status==="rejected"?C.red:a.status==="scored"?C.accent:C.amber} /></td>
                    <td style={{ padding:"14px 16px", color:C.muted, fontSize:12 }}>{a.applied_at?.slice(0,10)}</td>
                    <td style={{ padding:"14px 16px" }}><button onClick={() => loadAppDetail(a.id)} style={{ padding:"6px 14px", borderRadius:8, border:`1px solid ${C.accent}30`, background:`${C.accent}08`, color:C.accent, cursor:"pointer", fontSize:11, fontWeight:600, fontFamily:"'DM Sans'" }}>View Details</button></td>
                  </tr>
                ))}</tbody>
              </table>
              {applications.length === 0 && <div style={{ textAlign:"center", color:C.muted, padding:40, fontSize:13 }}>No applications yet</div>}
            </GlassCard>
          </div>
        )}

        {/* ═══ SCORE DETAILS ═══ */}
        {tab === "score-details" && (
          <div>
            <h2 style={{ fontSize:20, fontWeight:700, marginBottom:16, letterSpacing:"-0.02em" }}>Score Details</h2>
            {selectedApp?.score ? (
              <div>
                <GlassCard glow style={{ marginBottom:16, borderLeft:`3px solid ${selectedApp.score.overall_score >= 80 ? C.green : selectedApp.score.overall_score >= 60 ? C.amber : C.red}` }}>
                  <h3 style={{ fontWeight:700, fontSize:18, marginBottom:14, letterSpacing:"-0.02em" }}>{selectedApp.job?.title} — Score Breakdown</h3>
                  <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:20 }}>
                    <StatCard value={`${selectedApp.score.hard_req_score}%`} label="Hard Requirements" color={selectedApp.score.hard_req_passed?C.green:C.red} icon="◆" />
                    <StatCard value={`${selectedApp.score.ensemble_score}%`} label="ML Ensemble" color={C.accent} icon="◈" />
                    <StatCard value={`${selectedApp.score.overall_score}%`} label="Overall Score" color={C.purple} icon="★" />
                  </div>

                  {/* Model Cards - Expandable */}
                  <h4 style={{ fontSize:14, fontWeight:700, marginBottom:12 }}>How Each Model Decided</h4>
                  <div style={{ display:"grid", gridTemplateColumns:"1fr", gap:8, marginBottom:20 }}>
                    {[
                      { name:"Logistic Regression", score:selectedApp.score.logistic_regression_score, weight:"10%", icon:"📐", why:"Baseline — simple, fast, interpretable", how:"Assigns weight to each BERT feature. Sigmoid function converts to probability.", decided:s=>s>=80?"High positive weights pushed score above threshold.":s>=60?"Mixed weights — moderate confidence.":"Combined weights fell below threshold.", strength:"Fast. Clear feature importance." },
                      { name:"Naive Bayes", score:selectedApp.score.naive_bayes_score, weight:"10%", icon:"🎲", why:"Probabilistic — Bayes' theorem for match probability", how:"Estimates probability distribution per feature, multiplies together.", decided:s=>s>=80?"Feature distributions match 'good match' data.":s>=60?"Some distributions overlap between classes.":"Features resemble 'not match' examples.", strength:"Extremely fast. Good with limited data." },
                      { name:"KNN", score:selectedApp.score.knn_score, weight:"10%", icon:"📍", why:"Instance-based — finds 7 most similar training CVs", how:"Cosine distance in BERT space. Majority vote of 7 neighbors.", decided:s=>s>=80?"Most neighbors were good matches — similar to successful CVs.":s>=60?"Neighbors were mixed — borderline.":"Nearest CVs were NOT good matches.", strength:"Captures complex boundaries." },
                      { name:"Random Forest", score:selectedApp.score.random_forest_score, weight:"20%", icon:"🌲", why:"200 trees vote together — robust through ensemble", how:"Each tree trained on random subset. Majority vote wins.", decided:s=>s>=80?"Strong majority voted 'good match'.":s>=60?"Trees were split — ~60% voted match.":"Most trees voted 'not match'.", strength:"Very robust. Hard to overfit." },
                      { name:"SVM", score:selectedApp.score.svm_score, weight:"15%", icon:"🔲", why:"Optimal boundary in high-dimensional BERT space", how:"RBF kernel maps features to higher dimensions. Maximum-margin hyperplane.", decided:s=>s>=80?"CV clearly on 'good match' side of boundary.":s>=60?"Near the decision boundary.":"On 'no match' side of boundary.", strength:"Excellent with 384-dim BERT features." },
                      { name:"XGBoost", score:selectedApp.score.xgboost_score, weight:"35%", icon:"🚀", why:"Best performer — each tree corrects previous errors", how:"300 sequential trees. Each fixes mistakes of previous ones.", decided:s=>s>=80?"After 300 rounds, confidently predicts match.":s>=60?"Moderate confidence — later trees added uncertainty.":"Converged on 'not match' after 300 rounds.", strength:"Highest accuracy. Gets 35% ensemble weight." },
                    ].map(m => {
                      const sc = m.score||0, col = sc>=80?C.green:sc>=60?C.amber:C.red, exp = expandedModel===m.name;
                      return (
                        <div key={m.name} onClick={() => setExpandedModel(exp?null:m.name)} style={{ background:C.surfaceAlt, borderRadius:12, padding:14, border:`1px solid ${exp?C.borderLight:C.border}`, cursor:"pointer", transition:"all 0.25s" }}>
                          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
                            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                              <span style={{ fontSize:18 }}>{m.icon}</span>
                              <span style={{ fontSize:13, fontWeight:700 }}>{m.name}</span>
                              <span style={{ fontSize:10, color:C.muted, padding:"2px 8px", borderRadius:4, background:`${C.border}50` }}>Weight: {m.weight}</span>
                            </div>
                            <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                              <span style={{ fontSize:18, fontWeight:800, color:col }}>{sc}%</span>
                              <span style={{ fontSize:10, color:C.muted, transition:"transform 0.2s", transform:exp?"rotate(90deg)":"rotate(0)" }}>▸</span>
                            </div>
                          </div>
                          <Bar pct={sc} color={col} height={4} />
                          {exp && (
                            <div style={{ marginTop:12, fontSize:12, lineHeight:1.9, color:C.dim, animation:"fadeUp 0.2s ease" }}>
                              <div style={{ marginBottom:4 }}><span style={{ color:C.accent, fontWeight:600 }}>WHY:</span> {m.why}</div>
                              <div style={{ marginBottom:4 }}><span style={{ color:C.purple, fontWeight:600 }}>HOW:</span> {m.how}</div>
                              <div style={{ padding:10, borderRadius:8, background:`${col}08`, border:`1px solid ${col}18`, marginTop:6 }}>
                                <span style={{ color:col, fontWeight:600 }}>DECISION:</span> {m.decided(sc)}
                              </div>
                              <div style={{ marginTop:6, fontSize:10, color:C.muted, fontStyle:"italic" }}>Strength: {m.strength}</div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  {/* Score Formula */}
                  <GlassCard style={{ padding:14, marginBottom:16, background:C.surfaceAlt }}>
                    <h4 style={{ fontSize:13, fontWeight:700, marginBottom:10 }}>Score Calculation</h4>
                    <div style={{ padding:12, borderRadius:8, background:C.bg, fontFamily:"'JetBrains Mono'", fontSize:12, lineHeight:2, color:C.dim }}>
                      {selectedApp.score.hard_req_passed ? (
                        <div><div style={{ color:C.green }}>✓ Hard requirements PASSED</div><div>Overall = (30% × {selectedApp.score.hard_req_score}%) + (70% × {selectedApp.score.ensemble_score}%)</div><div style={{ color:C.accent, fontWeight:700 }}>= {selectedApp.score.overall_score}%</div></div>
                      ) : (
                        <div><div style={{ color:C.red }}>✗ Hard requirements FAILED — capped at 50%</div><div>Overall = (50% × {selectedApp.score.hard_req_score}%) + (50% × {selectedApp.score.ensemble_score}%)</div><div style={{ color:C.red, fontWeight:700 }}>= {selectedApp.score.overall_score}% (capped)</div></div>
                      )}
                    </div>
                  </GlassCard>

                  {/* SHAP Explanation */}
                  {selectedApp.score.shap_explanation && (() => {
                    const sh = selectedApp.score.shap_explanation;
                    const sel = sh.selected_because || sh.positive_factors || [];
                    const rej = sh.rejected_because || sh.negative_factors || [];
                    const sug = sh.improvement_suggestions || [];
                    return (
                    <div>
                      <h4 style={{ fontSize:14, fontWeight:700, marginBottom:12 }}>Why Your CV Got This Score</h4>
                      {sh.summary && <GlassCard style={{ padding:14, marginBottom:12, background:C.surfaceAlt, borderLeft:`3px solid ${C.accent}` }}><p style={{ fontSize:13, color:C.dim, lineHeight:1.8 }}>{sh.summary}</p></GlassCard>}

                      {sel.length > 0 && (
                        <GlassCard style={{ padding:14, marginBottom:10, background:`${C.green}04`, borderLeft:`3px solid ${C.green}` }}>
                          <div style={{ fontSize:13, fontWeight:700, color:C.green, marginBottom:10 }}>✅ Points Gained</div>
                          {sel.map((f,i) => <div key={i} style={{ display:"flex", justifyContent:"space-between", fontSize:12, color:C.dim, marginBottom:8, paddingLeft:10, borderLeft:`2px solid ${C.green}25` }}><div><div style={{ fontWeight:600 }}>{f.factor}</div>{f.type && <div style={{ fontSize:10, color:C.muted }}>Category: {f.type}</div>}{f.details?.map((d,j) => <div key={j} style={{ fontSize:10, color:C.muted }}>  {d}</div>)}</div><span style={{ color:C.green, fontWeight:700, minWidth:50, textAlign:"right" }}>{f.impact}</span></div>)}
                        </GlassCard>
                      )}

                      {rej.length > 0 && (
                        <GlassCard style={{ padding:14, marginBottom:10, background:`${C.red}04`, borderLeft:`3px solid ${C.red}` }}>
                          <div style={{ fontSize:13, fontWeight:700, color:C.red, marginBottom:10 }}>❌ Points Lost</div>
                          {rej.map((f,i) => <div key={i} style={{ display:"flex", justifyContent:"space-between", fontSize:12, color:C.dim, marginBottom:8, paddingLeft:10, borderLeft:`2px solid ${C.red}25` }}><div><div style={{ fontWeight:600 }}>{f.factor}</div>{f.mandatory && <span style={{ fontSize:10, color:C.red, fontWeight:600 }}> (MANDATORY)</span>}</div><span style={{ color:C.red, fontWeight:700, minWidth:50, textAlign:"right" }}>{f.impact}</span></div>)}
                        </GlassCard>
                      )}

                      {sh.bias_info && (
                        <GlassCard style={{ padding:12, marginBottom:10, background:`${C.purple}04`, borderLeft:`3px solid ${C.purple}` }}>
                          <div style={{ fontSize:12, fontWeight:600, color:C.purple, marginBottom:4 }}>🛡️ Bias Mitigation</div>
                          <div style={{ fontSize:11, color:C.dim }}>{sh.bias_info.message}</div>
                          {sh.bias_info.items_removed?.map((it,i) => <div key={i} style={{ fontSize:10, color:C.muted, marginTop:2 }}>• {it}</div>)}
                        </GlassCard>
                      )}

                      {sug.length > 0 && (
                        <GlassCard style={{ padding:14, background:`${C.amber}04`, borderLeft:`3px solid ${C.amber}` }}>
                          <div style={{ fontSize:13, fontWeight:700, color:C.amber, marginBottom:10 }}>💡 How to Improve</div>
                          {sug.map((s,i) => <div key={i} style={{ fontSize:12, color:C.dim, marginBottom:6, paddingLeft:10 }}>→ {s}</div>)}
                        </GlassCard>
                      )}
                    </div>);
                  })()}
                </GlassCard>
              </div>
            ) : (
              <GlassCard style={{ textAlign:"center", padding:50 }}>
                <div style={{ fontSize:36, marginBottom:12, opacity:0.3 }}>◈</div>
                <div style={{ color:C.muted, fontSize:14 }}>Select an application from "My Applications" to view details</div>
              </GlassCard>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
