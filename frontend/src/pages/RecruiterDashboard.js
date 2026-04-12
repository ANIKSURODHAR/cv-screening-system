import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { jobsAPI, candidatesAPI } from "../utils/api";

const P = {
  bg: "#faf8f5", surface: "#ffffff", surfaceAlt: "#f5f1ea", surfaceHover: "#f0ebe2",
  border: "#e8e2d8", borderLight: "#ded6c8",
  gold: "#c9a227", goldLight: "#e8d5a0", goldBg: "linear-gradient(145deg, #f5ecd7, #faf6ed)",
  dark: "#1a1a1a", text: "#2d2d2d", dim: "#6b6b6b", muted: "#9a9082",
  green: "#16a34a", greenBg: "#f0fdf4", greenBorder: "#bbf7d0",
  red: "#dc2626", redBg: "#fef2f2", redBorder: "#fecaca",
  amber: "#d97706", amberBg: "#fffbeb", amberBorder: "#fde68a",
  blue: "#2563eb", blueBg: "#eff6ff", blueBorder: "#bfdbfe",
  purple: "#7c3aed", purpleBg: "#f5f3ff", purpleBorder: "#ddd6fe",
};

const GlobalStyle = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@400;500;600;700&display=swap');
    * { margin:0; padding:0; box-sizing:border-box; }
    ::-webkit-scrollbar { width:5px; }
    ::-webkit-scrollbar-track { background:${P.bg}; }
    ::-webkit-scrollbar-thumb { background:${P.border}; border-radius:4px; }
    @keyframes fadeUp { from { opacity:0; transform:translateY(14px); } to { opacity:1; transform:translateY(0); } }
    @keyframes slideIn { from { opacity:0; transform:translateX(20px); } to { opacity:1; transform:translateX(0); } }
    .hover-card:hover { border-color:${P.borderLight} !important; transform:translateY(-2px); box-shadow:0 8px 30px rgba(0,0,0,0.06); }
    .hover-card { transition:all 0.25s; }
    .hover-row:hover { background:${P.surfaceHover} !important; }
    input:focus,textarea:focus { outline:none; border-color:${P.gold} !important; box-shadow:0 0 0 3px ${P.gold}18; }
  `}</style>
);

const Badge = ({ label, color, bg }) => <span style={{ display:"inline-flex", padding:"4px 12px", borderRadius:20, fontSize:11, fontWeight:600, fontFamily:"'DM Sans'", background:bg||`${color}10`, color, border:`1px solid ${color}25` }}>{label}</span>;
const Bar = ({ pct, color, h=6 }) => <div style={{ height:h, borderRadius:h, background:`${color}15`, width:"100%", overflow:"hidden" }}><div style={{ height:"100%", width:`${Math.min(pct,100)}%`, borderRadius:h, background:color, transition:"width 0.8s" }} /></div>;
const Card = ({ children, style={}, className="", ...p }) => <div className={className} style={{ background:P.surface, border:`1px solid ${P.border}`, borderRadius:16, padding:22, ...style }} {...p}>{children}</div>;
const StatCard = ({ value, label, color, bg, icon }) => <div style={{ background:bg||P.surface, border:`1px solid ${P.border}`, borderRadius:14, padding:18, position:"relative" }}><div style={{ position:"absolute", top:12, right:16, fontSize:24, opacity:0.12 }}>{icon}</div><div style={{ fontSize:30, fontWeight:800, color, fontFamily:"'DM Sans'" }}>{value}</div><div style={{ fontSize:11, color:P.muted, textTransform:"uppercase", letterSpacing:"0.06em", marginTop:4, fontWeight:500 }}>{label}</div></div>;

const ScoreRing = ({ score, size=90 }) => {
  const color = score>=80?P.green:score>=60?P.amber:P.red;
  const r=(size-10)/2, circ=2*Math.PI*r, off=circ-(score/100)*circ;
  return <div style={{ position:"relative", width:size, height:size }}><svg width={size} height={size} style={{ transform:"rotate(-90deg)" }}><circle cx={size/2} cy={size/2} r={r} fill="none" stroke={`${color}18`} strokeWidth={7} /><circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={7} strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={off} style={{ transition:"stroke-dashoffset 1.2s" }} /></svg><div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center" }}><div style={{ fontSize:size*0.26, fontWeight:800, color }}>{score}%</div><div style={{ fontSize:9, color:P.muted, textTransform:"uppercase", fontWeight:600 }}>{score>=80?"High":score>=60?"Medium":"Low"}</div></div></div>;
};

export default function RecruiterDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("dashboard");
  const [myJobs, setMyJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [applicants, setApplicants] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [candidateDetail, setCandidateDetail] = useState(null);
  const [jobForm, setJobForm] = useState({ title:"", company:user?.company||"", description:"", salary_range:"", hard_requirements:"" });
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => { loadMyJobs(); }, []);
  const loadMyJobs = async () => { try { const r = await jobsAPI.getMyJobs(); setMyJobs(r.data.results||r.data); } catch(e){} };
  const loadApplicants = async (jid) => { try { const r = await candidatesAPI.getApplicants(jid); setApplicants(r.data.results||r.data); } catch(e){} };
  const loadDetail = async (id) => { try { const r = await candidatesAPI.getApplicantDetail(id); setCandidateDetail(r.data); setSelectedCandidate(id); } catch(e){} };
  const handlePostJob = async (e) => {
    e.preventDefault(); setLoading(true); setMsg("");
    try {
      const reqs = jobForm.hard_requirements.split(",").filter(Boolean).map(r => ({ requirement_type:"skill", description:r.trim(), keywords:r.trim().toLowerCase(), is_mandatory:true }));
      await jobsAPI.createJob({...jobForm, hard_requirements:reqs});
      setMsg("Job submitted for admin approval!"); setJobForm({ title:"", company:user?.company||"", description:"", salary_range:"", hard_requirements:"" }); loadMyJobs();
    } catch(e) { setMsg("Error: " + (e.response?.data?.detail || JSON.stringify(e.response?.data))); } finally { setLoading(false); }
  };
  const handleStatus = async (id, st) => { try { await candidatesAPI.updateStatus(id, { status:st }); loadApplicants(selectedJob.id); if(candidateDetail?.id===id) loadDetail(id); } catch(e) { alert("Failed"); } };
  const totalApps = myJobs.reduce((a,j) => a+(j.applicant_count||0), 0);
  const inp = { width:"100%", padding:"12px 16px", borderRadius:12, border:`1.5px solid ${P.border}`, background:P.surfaceAlt, color:P.dark, fontSize:14, fontFamily:"'DM Sans'" };

  return (
    <div style={{ background:P.bg, minHeight:"100vh", color:P.text, fontFamily:"'DM Sans',sans-serif" }}>
      <GlobalStyle />
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"14px 28px", borderBottom:`1px solid ${P.border}`, background:P.surface, position:"sticky", top:0, zIndex:10 }}>
        <div style={{ display:"flex", alignItems:"center", gap:16 }}><span style={{ fontSize:20, fontWeight:700, fontFamily:"'Playfair Display',serif", padding:"6px 18px", border:`1.5px solid ${P.border}`, borderRadius:30 }}>CV.SCREEN</span><Badge label="Recruiter" color={P.purple} bg={P.purpleBg} /></div>
        <div style={{ display:"flex", alignItems:"center", gap:16 }}><div style={{ textAlign:"right" }}><div style={{ fontSize:14, fontWeight:600 }}>{user?.first_name} {user?.last_name}</div><div style={{ fontSize:11, color:P.muted }}>{user?.company||user?.email}</div></div><button onClick={logout} style={{ padding:"8px 18px", borderRadius:10, border:`1.5px solid ${P.red}25`, cursor:"pointer", fontSize:12, fontWeight:600, fontFamily:"'DM Sans'", background:P.redBg, color:P.red }}>Logout</button></div>
      </div>
      <div style={{ display:"flex", gap:2, padding:"14px 28px 0", background:P.surface, borderBottom:`1px solid ${P.border}` }}>
        {[["dashboard","Dashboard","◫"],["post-job","Post Job","＋"],["applicants","Applicants","◎"]].map(([k,l,ic]) => <button key={k} onClick={() => setTab(k)} style={{ padding:"10px 24px", borderRadius:"12px 12px 0 0", border:"none", cursor:"pointer", fontSize:13, fontWeight:600, fontFamily:"'DM Sans'", background:tab===k?P.bg:P.surface, color:tab===k?P.gold:P.muted, borderBottom:tab===k?`2px solid ${P.gold}`:"2px solid transparent" }}><span style={{ marginRight:8, opacity:0.5 }}>{ic}</span>{l}</button>)}
      </div>
      <div style={{ padding:"24px 28px", maxHeight:"calc(100vh - 120px)", overflowY:"auto" }}>

        {tab==="dashboard" && <div style={{ animation:"fadeUp 0.4s ease" }}>
          <h2 style={{ fontSize:24, fontWeight:700, fontFamily:"'Playfair Display',serif", marginBottom:20 }}>My Dashboard</h2>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:14, marginBottom:24 }}>
            <StatCard value={myJobs.length} label="My Jobs" color={P.blue} bg={P.blueBg} icon="◫" />
            <StatCard value={totalApps} label="Total Applicants" color={P.green} bg={P.greenBg} icon="◎" />
            <StatCard value={myJobs.filter(j=>j.status==="pending").length} label="Pending" color={P.amber} bg={P.amberBg} icon="⏳" />
          </div>
          {myJobs.map((j,i) => <Card key={j.id} className="hover-card" style={{ cursor:"pointer", marginBottom:12, borderLeft:`4px solid ${j.status==="approved"?P.green:j.status==="pending"?P.amber:P.red}`, animation:`fadeUp 0.3s ease ${i*0.06}s both` }} onClick={() => { setSelectedJob(j); loadApplicants(j.id); setTab("applicants"); setSelectedCandidate(null); setCandidateDetail(null); }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <div><div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:6 }}><span style={{ fontSize:16, fontWeight:700 }}>{j.title}</span><Badge label={j.status?.toUpperCase()} color={j.status==="approved"?P.green:j.status==="pending"?P.amber:P.red} bg={j.status==="approved"?P.greenBg:j.status==="pending"?P.amberBg:P.redBg} /></div><div style={{ fontSize:12, color:P.dim }}>{j.company} {j.salary_range&&<span style={{ color:P.green, fontWeight:600 }}>· 💰 {j.salary_range}</span>}</div></div>
              <div style={{ display:"flex", alignItems:"center", gap:8 }}><span style={{ fontSize:13, color:P.dim }}>{j.applicant_count||0} applicants</span><span style={{ color:P.gold, fontSize:18 }}>→</span></div>
            </div>
            <div style={{ marginTop:10, display:"flex", flexWrap:"wrap", gap:4 }}>{j.hard_requirements?.map(r => <span key={r.id} style={{ padding:"3px 10px", borderRadius:8, fontSize:10, fontWeight:600, background:P.blueBg, color:P.blue, border:`1px solid ${P.blueBorder}` }}>{r.description}</span>)}</div>
          </Card>)}
          {myJobs.length===0 && <Card style={{ textAlign:"center", padding:50, color:P.muted }}>No jobs yet. Click "Post Job" to get started.</Card>}
        </div>}

        {tab==="post-job" && <div style={{ maxWidth:600, animation:"fadeUp 0.4s ease" }}>
          <h2 style={{ fontSize:24, fontWeight:700, fontFamily:"'Playfair Display',serif", marginBottom:20 }}>Create new job posting</h2>
          <Card>
            {msg && <div style={{ padding:"12px 16px", borderRadius:12, marginBottom:16, background:msg.startsWith("Error")?P.redBg:P.greenBg, border:`1px solid ${msg.startsWith("Error")?P.redBorder:P.greenBorder}`, color:msg.startsWith("Error")?P.red:P.green, fontSize:13 }}>{msg}</div>}
            <form onSubmit={handlePostJob} style={{ display:"flex", flexDirection:"column", gap:16 }}>
              <div><label style={{ display:"block", fontSize:12, color:P.muted, marginBottom:6, fontWeight:500 }}>Job title</label><input style={inp} value={jobForm.title} onChange={e=>setJobForm({...jobForm,title:e.target.value})} placeholder="e.g. Senior Backend Developer" required /></div>
              <div><label style={{ display:"block", fontSize:12, color:P.muted, marginBottom:6, fontWeight:500 }}>Company</label><input style={inp} value={jobForm.company} onChange={e=>setJobForm({...jobForm,company:e.target.value})} required /></div>
              <div><label style={{ display:"block", fontSize:12, color:P.muted, marginBottom:6, fontWeight:500 }}>Salary range</label><input style={inp} value={jobForm.salary_range} onChange={e=>setJobForm({...jobForm,salary_range:e.target.value})} placeholder="e.g. 50,000 - 80,000 BDT/month" /></div>
              <div><label style={{ display:"block", fontSize:12, color:P.muted, marginBottom:6, fontWeight:500 }}>Description</label><textarea style={{...inp,minHeight:90,resize:"vertical"}} value={jobForm.description} onChange={e=>setJobForm({...jobForm,description:e.target.value})} placeholder="Describe the role..." required /></div>
              <div><label style={{ display:"block", fontSize:12, color:P.muted, marginBottom:6, fontWeight:500 }}>Must-have requirements (comma separated)</label><input style={inp} value={jobForm.hard_requirements} onChange={e=>setJobForm({...jobForm,hard_requirements:e.target.value})} placeholder="e.g. Python 3+ yrs, Node.js" required /><div style={{ fontSize:11, color:P.amber, marginTop:6, padding:"8px 12px", borderRadius:8, background:P.amberBg, border:`1px solid ${P.amberBorder}` }}>⚠ Candidates MUST match ALL. Failing = score capped at 50%.</div></div>
              <button type="submit" disabled={loading} style={{ padding:"14px", borderRadius:14, border:"none", background:P.goldBg, color:P.dark, fontSize:15, fontWeight:600, fontFamily:"'DM Sans'", cursor:"pointer", boxShadow:"0 4px 20px rgba(201,162,39,0.12)", opacity:loading?0.6:1 }}>{loading?"Submitting...":"Submit for Admin Approval"}</button>
              <div style={{ fontSize:12, color:P.muted, textAlign:"center" }}>Jobs go live only after Admin approves.</div>
            </form>
          </Card>
        </div>}

        {tab==="applicants" && <div style={{ animation:"fadeUp 0.3s ease" }}>
          {selectedJob && <Card style={{ marginBottom:18, borderLeft:`4px solid ${P.gold}` }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
              <div><div style={{ fontSize:18, fontWeight:700, fontFamily:"'Playfair Display',serif" }}>{selectedJob.title}</div><div style={{ fontSize:12, color:P.dim, marginTop:4 }}>{selectedJob.company} · {selectedJob.created_at?.slice(0,10)} {selectedJob.salary_range&&<span style={{ color:P.green, fontWeight:600, marginLeft:6 }}>💰 {selectedJob.salary_range}</span>}</div></div>
              <Badge label={`${applicants.length} applicants`} color={P.blue} bg={P.blueBg} />
            </div>
            <div style={{ marginTop:10 }}>{selectedJob.hard_requirements?.map(r => <span key={r.id} style={{ display:"inline-block", padding:"3px 10px", borderRadius:8, fontSize:10, fontWeight:600, background:P.blueBg, color:P.blue, marginRight:6, border:`1px solid ${P.blueBorder}` }}>{r.description}</span>)}</div>
          </Card>}

          <div style={{ display:"flex", gap:18 }}>
            <div style={{ width:candidateDetail?"42%":"100%", transition:"width 0.3s" }}>
              <Card style={{ padding:0, overflow:"hidden" }}>
                <div style={{ padding:"14px 18px", background:P.surfaceAlt, borderBottom:`1px solid ${P.border}`, display:"flex", justifyContent:"space-between" }}><span style={{ fontSize:14, fontWeight:700 }}>AI-Ranked Applicants</span><span style={{ fontSize:11, color:P.muted }}>Click to see details →</span></div>
                {applicants.map((a,i) => { const sc=a.overall_score||0, col=sc>=80?P.green:sc>=60?P.amber:P.red, sel=selectedCandidate===a.id;
                  return <div key={a.id} className="hover-row" onClick={() => loadDetail(a.id)} style={{ display:"flex", alignItems:"center", gap:14, padding:"14px 18px", cursor:"pointer", borderBottom:`1px solid ${P.border}08`, borderLeft:sel?`4px solid ${P.gold}`:"4px solid transparent", background:sel?`${P.gold}06`:"transparent", transition:"all 0.2s" }}>
                    <div style={{ width:32, height:32, borderRadius:"50%", display:"flex", alignItems:"center", justifyContent:"center", fontSize:13, fontWeight:800, background:i===0?P.greenBg:P.surfaceAlt, color:i===0?P.green:P.muted, border:`1px solid ${i===0?P.greenBorder:P.border}` }}>#{i+1}</div>
                    <div style={{ flex:1 }}><div style={{ fontSize:14, fontWeight:600 }}>{a.candidate_name}</div><div style={{ fontSize:11, color:P.muted }}>{a.candidate_email}</div></div>
                    {sc>0?<div style={{ textAlign:"right" }}><div style={{ fontSize:18, fontWeight:800, color:col }}>{sc}%</div><div style={{ fontSize:9, color:P.muted, fontWeight:600 }}>{sc>=80?"HIGH":sc>=60?"MED":"LOW"}</div></div>:<Badge label="Processing" color={P.amber} bg={P.amberBg} />}
                    <div style={{ display:"flex", gap:4 }}>
                      <button onClick={e=>{e.stopPropagation();handleStatus(a.id,"shortlisted")}} style={{ padding:"6px 10px", borderRadius:8, border:`1px solid ${P.greenBorder}`, background:P.greenBg, color:P.green, cursor:"pointer", fontSize:10, fontWeight:700 }}>✓</button>
                      <button onClick={e=>{e.stopPropagation();handleStatus(a.id,"rejected")}} style={{ padding:"6px 10px", borderRadius:8, border:`1px solid ${P.redBorder}`, background:P.redBg, color:P.red, cursor:"pointer", fontSize:10, fontWeight:700 }}>✗</button>
                    </div>
                  </div>;
                })}
                {applicants.length===0 && <div style={{ textAlign:"center", color:P.muted, padding:40 }}>No applicants yet</div>}
              </Card>
            </div>

            {candidateDetail?.score && <div style={{ flex:1, animation:"slideIn 0.3s ease" }}>
              <Card style={{ borderLeft:`4px solid ${candidateDetail.score.overall_score>=80?P.green:candidateDetail.score.overall_score>=60?P.amber:P.red}` }}>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:20, paddingBottom:18, borderBottom:`1px solid ${P.border}` }}>
                  <div><div style={{ fontSize:20, fontWeight:700, fontFamily:"'Playfair Display',serif" }}>{candidateDetail.candidate_name}</div><div style={{ fontSize:12, color:P.muted, marginTop:4 }}>Applied for {candidateDetail.job?.title}</div></div>
                  <ScoreRing score={candidateDetail.score.overall_score} />
                </div>

                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10, marginBottom:20 }}>
                  <div style={{ background:candidateDetail.score.hard_req_passed?P.greenBg:P.redBg, borderRadius:12, padding:14, textAlign:"center", border:`1px solid ${candidateDetail.score.hard_req_passed?P.greenBorder:P.redBorder}` }}><div style={{ fontSize:24, fontWeight:800, color:candidateDetail.score.hard_req_passed?P.green:P.red }}>{candidateDetail.score.hard_req_score}%</div><div style={{ fontSize:10, color:P.muted }}>REQUIREMENTS</div><div style={{ fontSize:10, color:candidateDetail.score.hard_req_passed?P.green:P.red, fontWeight:700, marginTop:4 }}>{candidateDetail.score.hard_req_passed?"✓ Passed":"✗ Failed"}</div></div>
                  <div style={{ background:P.blueBg, borderRadius:12, padding:14, textAlign:"center", border:`1px solid ${P.blueBorder}` }}><div style={{ fontSize:24, fontWeight:800, color:P.blue }}>{candidateDetail.score.ensemble_score}%</div><div style={{ fontSize:10, color:P.muted }}>AI ANALYSIS</div><div style={{ fontSize:10, color:P.dim, marginTop:4 }}>6 models voted</div></div>
                  <div style={{ background:P.purpleBg, borderRadius:12, padding:14, textAlign:"center", border:`1px solid ${P.purpleBorder}` }}><div style={{ fontSize:24, fontWeight:800, color:P.purple }}>{candidateDetail.score.overall_score}%</div><div style={{ fontSize:10, color:P.muted }}>FINAL SCORE</div></div>
                </div>

                <div style={{ background:P.surfaceAlt, borderRadius:12, padding:16, marginBottom:18, borderLeft:`4px solid ${P.blue}` }}>
                  <div style={{ fontSize:14, fontWeight:700, marginBottom:10 }}>How this score was calculated</div>
                  <div style={{ fontSize:13, lineHeight:2, color:P.dim }}>
                    {candidateDetail.score.hard_req_passed
                      ? <><div>1. Candidate <span style={{ color:P.green, fontWeight:700 }}>passed</span> requirements ({candidateDetail.score.hard_req_score}%)</div><div>2. AI analysis → {candidateDetail.score.ensemble_score}%</div><div>3. Final = 30% reqs + 70% AI = <span style={{ color:P.purple, fontWeight:700 }}>{candidateDetail.score.overall_score}%</span></div></>
                      : <><div>1. Candidate <span style={{ color:P.red, fontWeight:700 }}>failed</span> requirements ({candidateDetail.score.hard_req_score}%)</div><div>2. Score <span style={{ color:P.red, fontWeight:700 }}>capped at 50%</span></div><div>3. Final = <span style={{ color:P.red, fontWeight:700 }}>{candidateDetail.score.overall_score}%</span></div></>}
                  </div>
                </div>

                <div style={{ marginBottom:18 }}>
                  <div style={{ fontSize:14, fontWeight:700, marginBottom:6 }}>What each AI model said</div>
                  <div style={{ fontSize:12, color:P.muted, marginBottom:12, padding:10, borderRadius:10, background:P.surfaceAlt }}>6 models analyzed this CV. More accurate models get more voting power.</div>
                  {[
                    { n:"Logistic Regression", s:candidateDetail.score.logistic_regression_score, w:15, d:"Checks keyword overlap.", v:s=>s>=70?"Strong matches.":s>=50?"Some missing.":"Few matches." },
                    { n:"Naive Bayes", s:candidateDetail.score.naive_bayes_score, w:5, d:"Compares against past matches.", v:s=>s>=70?"Matches pattern.":s>=50?"Mixed signals.":"Doesn't match." },
                    { n:"KNN", s:candidateDetail.score.knn_score, w:10, d:"Finds 7 most similar CVs.", v:s=>s>=70?"Similar CVs were matches.":s>=50?"Mixed results.":"Similar CVs weren't matches." },
                    { n:"Random Forest", s:candidateDetail.score.random_forest_score, w:20, d:"200 experts vote.", v:s=>s>=70?"Majority of 200 voted yes.":s>=50?"Experts split.":"Most voted no." },
                    { n:"SVM", s:candidateDetail.score.svm_score, w:15, d:"Boundary between match/non-match.", v:s=>s>=70?"Clearly match side.":s>=50?"Near borderline.":"Non-match side." },
                    { n:"XGBoost", s:candidateDetail.score.xgboost_score, w:35, d:"Most accurate. Gets 35% weight.", v:s=>s>=70?"Confident match.":s>=50?"Uncertain.":"Not a strong match." },
                  ].map(m => { const sc=m.s||0, col=sc>=70?P.green:sc>=50?P.amber:P.red;
                    return <div key={m.n} style={{ background:P.surface, borderRadius:12, padding:14, marginBottom:8, border:`1px solid ${P.border}`, borderLeft:`4px solid ${col}` }}>
                      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}><div><span style={{ fontSize:13, fontWeight:700 }}>{m.n}</span><span style={{ fontSize:10, color:P.muted, marginLeft:8 }}>· {m.w}% weight</span></div><span style={{ fontSize:17, fontWeight:800, color:col }}>{sc}%</span></div>
                      <Bar pct={sc} color={col} h={5} />
                      <div style={{ fontSize:11, color:P.muted, marginTop:6, fontStyle:"italic" }}>{m.d}</div>
                      <div style={{ fontSize:12, marginTop:4, padding:"8px 12px", borderRadius:8, background:sc>=70?P.greenBg:sc>=50?P.amberBg:P.redBg, border:`1px solid ${sc>=70?P.greenBorder:sc>=50?P.amberBorder:P.redBorder}`, color:P.dim }}><span style={{ fontWeight:700, color:col }}>Verdict:</span> {m.v(sc)}</div>
                    </div>;
                  })}
                </div>

                {candidateDetail.score.shap_explanation && (() => {
                  const sh=candidateDetail.score.shap_explanation, sel=sh.selected_because||sh.positive_factors||[], rej=sh.rejected_because||sh.negative_factors||[], sug=sh.improvement_suggestions||[];
                  return <div>
                    <div style={{ fontSize:14, fontWeight:700, marginBottom:10 }}>CV analysis</div>
                    {sh.summary && <div style={{ padding:14, borderRadius:12, background:P.surfaceAlt, marginBottom:10, fontSize:13, color:P.dim, lineHeight:1.8, borderLeft:`4px solid ${P.blue}` }}>{sh.summary}</div>}
                    {sel.length>0 && <div style={{ padding:14, borderRadius:12, background:P.greenBg, marginBottom:10, border:`1px solid ${P.greenBorder}` }}><div style={{ fontSize:13, fontWeight:700, color:P.green, marginBottom:8 }}>✅ Strengths</div>{sel.map((f,i)=><div key={i} style={{ display:"flex", justifyContent:"space-between", fontSize:12, color:P.dim, marginBottom:6, paddingLeft:10, borderLeft:`2px solid ${P.greenBorder}` }}><span>{f.factor}</span><span style={{ color:P.green, fontWeight:700 }}>{f.impact}</span></div>)}</div>}
                    {rej.length>0 && <div style={{ padding:14, borderRadius:12, background:P.redBg, marginBottom:10, border:`1px solid ${P.redBorder}` }}><div style={{ fontSize:13, fontWeight:700, color:P.red, marginBottom:8 }}>❌ Gaps</div>{rej.map((f,i)=><div key={i} style={{ display:"flex", justifyContent:"space-between", fontSize:12, color:P.dim, marginBottom:6, paddingLeft:10, borderLeft:`2px solid ${P.redBorder}` }}><span>{f.factor}{f.mandatory&&<span style={{ color:P.red, fontSize:10 }}> (Required)</span>}</span><span style={{ color:P.red, fontWeight:700 }}>{f.impact}</span></div>)}</div>}
                    {sh.bias_info && <div style={{ padding:12, borderRadius:12, background:P.purpleBg, marginBottom:10, border:`1px solid ${P.purpleBorder}`, fontSize:12 }}><span style={{ fontWeight:700, color:P.purple }}>🛡️ Fair scoring:</span> <span style={{ color:P.dim }}>{sh.bias_info.message}</span></div>}
                    {sug.length>0 && <div style={{ padding:14, borderRadius:12, background:P.amberBg, border:`1px solid ${P.amberBorder}` }}><div style={{ fontSize:13, fontWeight:700, color:P.amber, marginBottom:8 }}>💡 Improvements</div>{sug.map((s,i)=><div key={i} style={{ fontSize:12, color:P.dim, marginBottom:4, paddingLeft:10 }}>→ {s}</div>)}</div>}
                  </div>;
                })()}

                {candidateDetail.cv_text?.skills_extracted?.length>0 && <div style={{ marginTop:16 }}><div style={{ fontSize:13, fontWeight:700, marginBottom:8 }}>Skills found</div><div style={{ display:"flex", flexWrap:"wrap", gap:4 }}>{candidateDetail.cv_text.skills_extracted.map((sk,i)=><span key={i} style={{ padding:"4px 12px", borderRadius:8, fontSize:11, fontWeight:600, background:P.greenBg, color:P.green, border:`1px solid ${P.greenBorder}` }}>{typeof sk==="string"?sk:sk.skill}</span>)}</div></div>}

                <div style={{ display:"flex", gap:10, marginTop:22, paddingTop:18, borderTop:`1px solid ${P.border}` }}>
                  <button onClick={()=>handleStatus(candidateDetail.id,"shortlisted")} style={{ flex:1, padding:"14px", borderRadius:14, border:"none", cursor:"pointer", fontSize:14, fontWeight:700, fontFamily:"'DM Sans'", background:P.green, color:"#fff", boxShadow:`0 4px 16px ${P.green}25` }}>✓ Shortlist</button>
                  <button onClick={()=>handleStatus(candidateDetail.id,"rejected")} style={{ flex:1, padding:"14px", borderRadius:14, border:`1.5px solid ${P.redBorder}`, cursor:"pointer", fontSize:14, fontWeight:700, fontFamily:"'DM Sans'", background:P.redBg, color:P.red }}>✗ Reject</button>
                </div>
              </Card>
            </div>}
          </div>
          {!selectedJob && <Card style={{ textAlign:"center", padding:50, color:P.muted }}>Select a job from Dashboard to view applicants</Card>}
        </div>}
      </div>
    </div>
  );
}
