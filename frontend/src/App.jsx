import React, { useEffect, useMemo, useState } from "react";
import {
    Home, Workflow, Search, BarChart3, Lightbulb, CircleDollarSign,
    Settings, ShieldCheck, FileText, CreditCard, ShoppingCart, XCircle,
    ChevronRight, ArrowRight, Zap, LockKeyhole, UserRound, Activity,
    Coins, WalletCards, CheckCircle2, Clock3, Filter, Download, Database,
    Bot, Gauge, PlayCircle, RefreshCw, Server, AlertTriangle, ExternalLink
} from "lucide-react";

const logoData = "data:image/png;base64,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";

function IntroPage({ onGetStarted }) {
    const features = [
        [Bot, "AI-Powered Diagnosis", "Understand why revenue is slipping away using payment and customer context."],
        [Zap, "Smart Recovery Decisions", "Select the recovery action with the strongest expected economic outcome."],
        [ShieldCheck, "Policy-Aware Automation", "Every recovery action passes deterministic safety and policy controls."],
        [CheckCircle2, "Verified Revenue", "Confirm actual recovery through Razorpay payment webhook events."],
        [FileText, "Complete Audit Trail", "Track every decision, action, policy check and recovery outcome."],
        [Gauge, "Recovery Economics", "Measure incremental recovery and optimize intervention costs."]
    ];

    return (
        <div className="intro-page">
            <div className="intro-orb intro-orb-one" />
            <div className="intro-orb intro-orb-two" />
            <div className="intro-grid" />

            <header className="intro-nav">
                <div className="intro-brand">
                    <div className="intro-logo">
                        <img src={logoData} alt="REVERA" />
                    </div>
                    <div>
                        <strong>REVERA</strong>
                        <span>Intelligent Revenue Recovery</span>
                    </div>
                </div>
                <div className="intro-status"><i /> RAZORPAY TEST MODE</div>
            </header>

            <main className="intro-main">
                <section className="intro-hero">
                    <div className="intro-badge"><span><Zap size={13} /></span> AI-POWERED REVENUE RECOVERY</div>
                    <h1>Recover the revenue<br /><em>you are about to lose.</em></h1>
                    <p>REVERA detects revenue leakage, diagnoses payment failures, chooses the best recovery strategy and verifies the money actually recovered.</p>
                    <div className="intro-actions">
                        <button className="intro-cta" onClick={onGetStarted}>Get Started <ArrowRight size={18} /></button>
                        <div className="intro-trust"><ShieldCheck size={15} /> Policy-aware &amp; auditable</div>
                    </div>
                    <div className="intro-flow">
                        {["Detect", "Decide", "Act", "Prove"].map((item, index) => (
                            <React.Fragment key={item}>
                                <div className="intro-flow-step"><small>0{index + 1}</small><b>{item}</b></div>
                                {index < 3 && <ArrowRight size={14} />}
                            </React.Fragment>
                        ))}
                    </div>
                </section>

                <section className="intro-features">
                    <div className="intro-section-heading">
                        <span>CORE CAPABILITIES</span>
                        <h2>Everything needed to win revenue back.</h2>
                        <p>One intelligent control plane from failed payment to verified recovery.</p>
                    </div>
                    <div className="intro-feature-grid">
                        {features.map(([Icon, title, text]) => (
                            <div className="intro-feature-card" key={title}>
                                <div className="intro-feature-icon"><Icon size={20} /></div>
                                <div><h3>{title}</h3><p>{text}</p></div>
                            </div>
                        ))}
                    </div>
                </section>
            </main>

            <footer className="intro-footer">
                <div><b>REVERA</b><span>Intelligent Revenue Recovery System</span></div>
                <div><span>Detect. Decide. Act. Prove.</span></div>
            </footer>
        </div>
    );
}

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

const fallbackCases = [
    { id: "RCP-1042", amount: 8499, event_type: "payment.failed", payment_method: "upi", recovery_probability: .78, recommended_action: "PAYMENT_LINK", failure_reason: "transient_failure", successful_payments: 7, failed_payments: 1, attempt_count: 1 },
    { id: "RCP-1043", amount: 12500, event_type: "checkout.abandoned", payment_method: "card", recovery_probability: .61, recommended_action: "REMINDER", failure_reason: null, successful_payments: 3, failed_payments: 0, attempt_count: 0 },
    { id: "RCP-1044", amount: 499, event_type: "payment.failed", payment_method: "upi", recovery_probability: .09, recommended_action: "STOP", failure_reason: "repeated_failure", successful_payments: 1, failed_payments: 6, attempt_count: 2 }
];

const nav = [
    ["dashboard", "Dashboard", Home],
    ["pipeline", "Recovery Pipeline", Workflow],
    ["cases", "Case Explorer", Search],
    ["insights", "AI Insights", Lightbulb],
    ["analytics", "Analytics", BarChart3],
    ["benchmark", "Benchmark Lab", Lightbulb],
    ["audit", "Audit Trail", CircleDollarSign],
    ["settings", "Settings", Settings]
];

const formatINR = value => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
const pct = value => `${Math.round(Number(value || 0) * 100)}%`;
const actionName = value => String(value || "N/A").replaceAll("_", " ");
const getId = item => item?.id || item?.case_id;

async function api(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
    const text = await response.text();
    let data = {};
    try { data = text ? JSON.parse(text) : {}; } catch { data = { detail: text }; }
    if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : data.detail?.message || JSON.stringify(data.detail || data);
        throw new Error(detail || `Request failed with ${response.status}`);
    }
    return data;
}

function Logo() {
    return <img src={logoData} className="logo-image" alt="REVERA logo" />;
}

function App() {
    const [page, setPage] = useState("dashboard");
    const [showIntro, setShowIntro] = useState(true);
    const [cases, setCases] = useState([]);
    const [selected, setSelected] = useState(null);
    const [decision, setDecision] = useState(null);
    const [execution, setExecution] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [auditEvents, setAuditEvents] = useState([]);
    const [benchmarkData, setBenchmarkData] = useState(null);
    const [backendOnline, setBackendOnline] = useState(false);
    const [loading, setLoading] = useState(true);
    const [decisionLoading, setDecisionLoading] = useState(false);
    const [executing, setExecuting] = useState(false);
    const [error, setError] = useState("");

    const refreshData = async () => {
        setLoading(true);
        setError("");
        try {
            const [caseData, analyticsData, auditData, benchmarkResult] = await Promise.all([
                api("/api/cases"),
                api("/api/analytics"),
                api("/api/audit?limit=100"),
                api("/api/benchmark?limit=1000&live=false")
            ]);
            const normalized = Array.isArray(caseData) ? caseData : [];
            setCases(normalized);
            setAnalytics(analyticsData);
            setAuditEvents(auditData?.events || []);
            setBenchmarkData({ ...(benchmarkResult?.revenue_recovery_benchmark || {}), cases: benchmarkResult?.cases ?? 0, seed: benchmarkResult?.seed });
            setBackendOnline(true);
            setSelected(current => {
                if (current) return normalized.find(x => getId(x) === getId(current)) || normalized[0] || null;
                return normalized[0] || null;
            });
        } catch (err) {
            setBackendOnline(false);
            setCases(fallbackCases);
            setSelected(current => current || fallbackCases[0]);
            setError(`Backend unavailable: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { refreshData(); }, []);

    useEffect(() => {
        setDecision(null);
        setExecution(null);
        if (!selected || !backendOnline) return;
        let cancelled = false;
        const run = async () => {
            setDecisionLoading(true);
            setError("");
            try {
                const data = await api("/api/recovery/decide", {
                    method: "POST",
                    body: JSON.stringify({
                        case_id: getId(selected),
                        customer_id: selected.customer_id || "CUS-UNKNOWN",
                        amount: Number(selected.amount || 0),
                        currency: selected.currency || "INR",
                        event_type: selected.event_type || "payment.failed",
                        payment_method: selected.payment_method || "upi",
                        failure_reason: selected.failure_reason || null,
                        attempts: Number(selected.attempt_count ?? selected.attempts ?? 0),
                        successes: Number(selected.successful_payments ?? selected.successes ?? 0),
                        failures: Number(selected.failed_payments ?? selected.failures ?? 0),
                        customer_age_days: Number(selected.customer_age_days || 180),
                        customer_lifetime_value: Number(selected.customer_lifetime_value || 5000),
                        days_since_last_payment: Number(selected.days_since_last_payment || 7),
                        checkout_duration_seconds: Number(selected.checkout_duration_seconds || 120),
                        prior_recovery_rate: Number(selected.prior_recovery_rate || 0),
                        contacts_24h: Number(selected.contacts_24h || 0),
                        hours_since_event: Number(selected.hours_since_event || 1)
                    })
                });
                if (!cancelled) setDecision(data);
            } catch (err) {
                if (!cancelled) setError(`Decision engine: ${err.message}`);
            } finally {
                if (!cancelled) setDecisionLoading(false);
            }
        };
        run();
        return () => { cancelled = true; };
    }, [selected, backendOnline]);

    const navigate = target => {
        setPage(target);
        setError("");
    };

    const openCase = item => {
        setSelected(item);
        setPage("dashboard");
        setExecution(null);
    };

    const executeRecovery = async () => {
        if (!selected || !decision) return;
        const action = decision.final_decision?.action || decision.risk?.recommendation || decision.economics?.recommended_action;
        const policy = decision.policy?.decision || "";
        if (action !== "PAYMENT_LINK") {
            setError("Only PAYMENT_LINK execution is currently enabled in Test Mode.");
            return;
        }
        if (policy !== "APPROVED") {
            setError("Recovery cannot execute until deterministic policy authorization is APPROVED.");
            return;
        }
        setExecuting(true);
        setError("");
        try {
            const result = await api("/api/recovery/execute", {
                method: "POST",
                body: JSON.stringify({
                    case_id: getId(selected),
                    customer_id: selected.customer_id || "CUS-UNKNOWN",
                    amount: Number(selected.amount || 0),
                    currency: selected.currency || "INR",
                    action,
                    policy_status: "approved",
                    customer_name: selected.customer_name || "Demo Customer",
                    customer_email: selected.customer_email || "demo@example.com",
                    customer_contact: selected.customer_contact || "9876543210"
                })
            });
            setExecution(result);
            await refreshData();
            const audit = await api("/api/audit?limit=100");
            setAuditEvents(audit?.events || []);
        } catch (err) {
            setError(`Execution: ${err.message}`);
        } finally {
            setExecuting(false);
        }
    };

    const runBenchmark = async () => {
        try {
            setError("");
            const result = await api("/api/benchmark?limit=1000&live=false");
            setBenchmarkData({ ...(result?.revenue_recovery_benchmark || {}), cases: result?.cases ?? 0, seed: result?.seed });
        } catch (err) {
            setError(`Benchmark: ${err.message}`);
        }
    };

    const navProps = { page, navigate };

    const handleGetStarted = () => {
        setShowIntro(false);
    };

    if (showIntro) return <IntroPage onGetStarted={handleGetStarted} />;

    return (
        <div className="app">
            <Sidebar {...navProps} backendOnline={backendOnline} />
            <main className="main">
                {!backendOnline && !loading && <div className="connection-banner"><AlertTriangle size={15} /><span>Backend connection is offline. Showing fallback UI.</span><button onClick={refreshData}>Retry</button></div>}
                {page === "dashboard" && <Dashboard selected={selected || fallbackCases[0]} cases={cases.length ? cases : fallbackCases} decision={decision} decisionLoading={decisionLoading} execution={execution} executing={executing} analytics={analytics} onSelect={openCase} onExecute={executeRecovery} setPage={setPage} backendOnline={backendOnline} />}
                {page === "pipeline" && <Pipeline cases={cases.length ? cases : fallbackCases} selected={selected} decision={decision} decisionLoading={decisionLoading} execution={execution} executing={executing} onSelect={item => { setSelected(item); setExecution(null); }} onDecision={async () => { if (selected) { setPage("dashboard"); } }} onExecute={executeRecovery} backendOnline={backendOnline} />}
                {page === "cases" && <Cases cases={cases.length ? cases : fallbackCases} selected={selected} onSelect={item => { setSelected(item); setExecution(null); }} />}
                {page === "insights" && <Insights decision={decision} backendOnline={backendOnline} />}
                {page === "analytics" && <Analytics data={analytics} />}
                {page === "benchmark" && <Benchmark data={benchmarkData} onRun={runBenchmark} />}
                {page === "audit" && <Audit events={auditEvents} onRefresh={async () => { const data = await api("/api/audit?limit=100"); setAuditEvents(data?.events || []); }} />}
                {page === "settings" && <SettingsPage backendOnline={backendOnline} />}
                <Footer backendOnline={backendOnline} />
            </main>
        </div>
    );
}

function Sidebar({ page, navigate, backendOnline }) {
    return <aside className="sidebar">
        <div className="brand">
            <Logo />
            <div className="brand-name">REVERA</div>
            <div className="brand-subtitle">Intelligent Revenue<br />Recovery System</div>
            <div className="brand-line" />
        </div>
        <nav className="nav">
            {nav.map(([id, label, Icon]) => <button key={id} className={`nav-item ${page === id ? "active" : ""}`} onClick={() => navigate(id)}><Icon size={19} strokeWidth={1.8} /><span>{label}</span></button>)}
        </nav>
        <div className="side-slogan"><b>Recover More</b><b>Grow Smarter</b><i /></div>
    </aside>;
}

function Header({ page = null }) {
    if (page) {
        const PageIcon = page.icon;
        return (
            <header className="page-header">
                <div className="page-header-icon">
                    <PageIcon size={25} />
                </div>
                <div>
                    <span>{page.eyebrow}</span>
                    <h1>{page.title}</h1>
                    <p>{page.description}</p>
                </div>
            </header>
        );
    }

    return <header className="hero">
        <div className="hero-copy">
            <h1>REVE<span>R</span>A</h1>
            <h2>Revenue Recovery Control Plane</h2>
            <p>Turn failed payments into recovered revenue with intelligent, policy-aware automation.</p>
            <strong>Detect. Decide. Act. Prove.</strong>
        </div>
        <div className="test-mode"><span className="test-dot" /><div><b>TEST MODE</b><small>Razorpay Sandbox</small></div></div>
        <div className="mountains"><i /><b /><em /></div>
        <div className="hero-message"><span>TURNING</span><b>FAILED PAYMENTS</b><b>INTO REAL REVENUE</b><i /></div>
    </header>;
}

function Stat({ icon: Icon, theme, title, value, change, text }) {
    return <div className="stat-card"><div className={`stat-icon ${theme}`}><Icon size={27} /></div><div className="stat-copy"><span>{title}</span><strong>{value}</strong><small>{change ? <><b>{change}</b> {text}</> : text}</small></div>{theme !== "purple" && theme !== "blue" && <div className={`mini-bars ${theme}`}>{[8, 15, 23, 31, 42].map((h, i) => <i key={i} style={{ height: `${h}px` }} />)}</div>}</div>;
}

function Dashboard({ selected, cases, decision, decisionLoading, execution, executing, analytics, onSelect, onExecute, setPage, backendOnline }) {
    const atRisk = cases.reduce((sum, c) => {
        const status = String(c.status || "").toLowerCase();
        return ["recovered", "stopped", "cancelled", "expired"].includes(status) ? sum : sum + Number(c.amount || 0);
    }, 0);
    const recovered = Number(analytics?.verified_recovered ?? analytics?.recovered ?? execution?.recovered_amount ?? 0);
    const probability = decision?.risk?.recovery_probability ?? selected.recovery_probability ?? 0;
    const action = decision?.final_decision?.action || decision?.economics?.recommended_action || selected.recommended_action || "STOP";
    const expected = decision?.final_decision?.selected_expected_recovery_value ?? decision?.economics?.expected_recovery_value ?? Number(selected.amount || 0) * probability;
    return <>
        <Header />
        <section className="stats">
            <Stat icon={CircleDollarSign} theme="gold" title="REVENUE AT RISK" value={formatINR(atRisk)} change="LIVE" text="from tracked cases" />
            <Stat icon={Coins} theme="green" title="VERIFIED RECOVERED" value={formatINR(recovered)} change="WEBHOOK" text="confirmed revenue" />
            <Stat icon={FileText} theme="purple" title="CASES" value={cases.length} text={`${cases.filter(c => !["recovered", "stopped", "cancelled", "expired"].includes(String(c.status || "").toLowerCase())).length} active`} />
            <Stat icon={ShieldCheck} theme="blue" title="POLICY STATUS" value="ENFORCED" text="deterministic guard" />
        </section>
        <section className="dashboard-grid">
            <div className="left">
                <div className="panel opportunities">
                    <div className="panel-head"><div><h3>Recovery Opportunities</h3><p>High-value cases identified by REVERA</p></div><button onClick={() => setPage("pipeline")}>View All <ArrowRight size={16} /></button></div>
                    <div className="opportunity-list">{cases.map(item => <Opportunity key={getId(item)} item={item} selected={getId(selected) === getId(item)} onClick={() => onSelect(item)} />)}</div>
                </div>
                <div className="lower-grid"><Trend cases={cases} /><Distribution cases={cases} /></div>
            </div>
            <Trace selected={selected} decision={decision} decisionLoading={decisionLoading} execution={execution} executing={executing} onExecute={onExecute} action={action} probability={probability} expected={expected} backendOnline={backendOnline} />
        </section>
    </>;
}

function Opportunity({ item, selected, onClick }) {
    const event = item.event_type || "payment.failed";
    const Icon = event.includes("checkout") ? ShoppingCart : event.includes("payment") ? XCircle : CreditCard;
    const type = event.includes("checkout") ? "cart" : event.includes("payment") ? "failed" : "card";
    return <button className={`opportunity ${selected ? "selected" : ""}`} onClick={onClick}><div className={`opp-icon ${type}`}><Icon size={21} /></div><div className="opp-info"><strong>{formatINR(item.amount)}</strong><span>{getId(item)} <i>•</i> {event}</span></div><div className="prob">{pct(item.recovery_probability)}</div><div className={`action ${String(item.recommended_action || "STOP").toLowerCase()}`}>{actionName(item.recommended_action || "STOP")}</div><ChevronRight size={20} /></button>;
}

function Trace({ selected, decision, decisionLoading, execution, executing, onExecute, action, probability, expected, backendOnline }) {
    const policy = decision?.policy?.decision || "PENDING";
    const diagnosis = decision?.investigator?.root_cause || selected.failure_reason || "Awaiting AI investigation";
    const customer = `${selected.successful_payments ?? 0} successful • ${selected.failed_payments ?? 0} failed`;
    const status = execution ? "Recovered" : policy === "APPROVED" ? "Decision Ready" : "Active";
    const rows = [
        [LockKeyhole, "Event", selected.event_type || "payment.failed", "gold"],
        [UserRound, "Customer Context", customer, "green"],
        [Activity, "AI Diagnosis", diagnosis, "green"],
        [Zap, "Recovery Probability", decisionLoading ? "Analyzing..." : pct(probability), "green"],
        [LockKeyhole, "Expected Recovery", formatINR(expected), "purple"],
        [WalletCards, "Recommended Action", actionName(action), "gold"],
        [LockKeyhole, "Policy Check", execution ? "Approved • Payment Link created" : policy === "APPROVED" ? "APPROVED • Deterministic authorization" : policy, "gold"]
    ];
    return <div className="panel trace">
        <div className="trace-head"><div><b>{getId(selected)}</b><h3>AI Decision Trace</h3></div><span><i />{status}</span></div>
        <div className="trace-list">{rows.map(([Icon, title, value, color], i) => <div className={`trace-row ${i === rows.length - 1 ? "last" : ""}`} key={title}><div className={`trace-icon ${color}`}><Icon size={16} /></div><div className="trace-connector" /><div className="trace-text"><b>{title}</b><span>{value}</span></div><time>{decision?.investigator?.latency_ms ? `${Math.round(decision.investigator.latency_ms)} ms` : "LIVE"}</time></div>)}</div>
        {decision?.investigator?.live && <div className="live-badge"><Bot size={13} /> Gemini Investigator Live • {decision.investigator.model}</div>}
        {execution?.payment_link && <div className="execution-success"><CheckCircle2 size={19} /><div><span>RAZORPAY TEST MODE</span><strong>Payment Link Created</strong></div><a href={execution.payment_link} target="_blank" rel="noreferrer">Open Link <ExternalLink size={13} /></a></div>}
        <button className={`execute ${execution ? "done" : ""}`} onClick={onExecute} disabled={executing || !!execution || !backendOnline || policy !== "APPROVED" || action !== "PAYMENT_LINK"}>{execution ? <><CheckCircle2 size={18} />Recovery Executed</> : executing ? <><RefreshCw className="spin" size={18} />Creating Payment Link...</> : <><Zap size={18} />Execute Recovery<ArrowRight size={18} /></>}</button>
    </div>;
}

function Trend({ cases }) {
    const vals = useMemo(() => cases.slice(0, 7).map(c => Number(c.recovered_amount || 0) / 1000 || 1), [cases]);
    const labels = ["Case 1", "Case 2", "Case 3", "Case 4", "Case 5", "Case 6", "Case 7"];
    return <div className="panel small-panel"><div className="small-head"><div><BarChart3 size={21} /><div><h3>Recovery Trend</h3><p>Verified recovery signal</p></div></div><button>Tracked cases <ChevronRight size={14} /></button></div><div className="chart"><div className="y"><span>30K</span><span>20K</span><span>10K</span><span>0</span></div><div className="bars">{vals.map((v, i) => <div className="bar-wrap" key={i}><i style={{ height: `${Math.max(5, Math.min(120, v * 4))}px` }} /><span>{labels[i]}</span></div>)}</div></div></div>;
}

function Distribution({ cases }) {
    const counts = cases.reduce((a, c) => { const k = c.recommended_action || "STOP"; a[k] = (a[k] || 0) + 1; return a; }, {});
    const total = Math.max(1, cases.length);
    const parts = [["PAYMENT_LINK", "Payment Link", "gold"], ["REMINDER", "Reminder", "gold2"], ["RETRY", "Retry", "white"], ["STOP", "Stop", "gray"]];
    return <div className="panel small-panel distribution"><div className="small-head"><div><Coins size={21} /><div><h3>Action Distribution</h3><p>Recommended actions by REVERA</p></div></div></div><div className="distribution-body"><div className="donut"><div><b>{cases.length}</b><span>Cases</span></div></div><div className="legend">{parts.map(([key, label, c]) => <Legend key={key} label={label} value={`${Math.round(((counts[key] || 0) / total) * 100)}%`} c={c} />)}</div></div></div>;
}

function Legend({ label, value, c }) { return <div><i className={c} /><span>{label}</span><b>{value}</b></div>; }

function Pipeline({ cases, selected, decision, decisionLoading, execution, executing, onSelect, onExecute, backendOnline }) {
    const current = selected || cases[0];
    const action = decision?.final_decision?.action || current?.recommended_action || "STOP";
    const policy = decision?.policy?.decision || "PENDING";
    return <><Header page={{ eyebrow: "RECOVERY OPERATIONS", title: "Recovery Pipeline", description: "Monitor, prioritize and execute revenue recovery opportunities.", icon: Workflow }} /><div className="page-content">
        <div className="summary-grid">{[["Open Opportunities", cases.length, Workflow], ["Value at Risk", formatINR(cases.reduce((s, c) => s + Number(c.amount || 0), 0)), CircleDollarSign], ["Avg. Recovery", cases.length ? `${Math.round(cases.reduce((s, c) => s + Number(c.recovery_probability || 0), 0) / cases.length * 100)}%` : "0%", Gauge], ["Policy Compliance", "100%", ShieldCheck]].map(([t, v, I]) => <div className="summary-card panel" key={t}><I size={22} /><div><span>{t}</span><b>{v}</b></div></div>)}</div>
        <div className="panel table-panel"><div className="panel-head"><div><h3>Active Recovery Queue</h3><p>Prioritized by tracked recovery value</p></div><button onClick={() => window.location.reload()}><RefreshCw size={15} />Refresh</button></div><div className="table"><div className="table-row head"><span>CASE</span><span>EVENT</span><span>AMOUNT</span><span>PROBABILITY</span><span>ACTION</span><span>STATUS</span></div>{cases.map(item => <button className={`table-row ${current && getId(current) === getId(item) ? "selected" : ""}`} key={getId(item)} onClick={() => onSelect(item)}><span className="gold-text">{getId(item)}</span><span>{item.event_type}</span><b>{formatINR(item.amount)}</b><span className="green-text">{pct(item.recovery_probability)}</span><span>{actionName(item.recommended_action)}</span><span className="status"><i />{item.status || "at_risk"}</span></button>)}</div></div>
        {current && <div className="panel pipeline-live"><div><span>SELECTED CASE</span><h3>{getId(current)} · {formatINR(current.amount)}</h3><p>{current.event_type} · {current.payment_method || "unknown"} · {current.failure_reason || "no failure reason"}</p></div><div className="pipeline-live-status">{decisionLoading ? "AI ANALYZING" : `${actionName(action)} · ${policy}`}</div><button onClick={onExecute} disabled={executing || !backendOnline || action !== "PAYMENT_LINK" || policy !== "APPROVED"}>{executing ? "Creating..." : execution ? "Payment Link Created" : "Execute Recovery"} <ArrowRight size={15} /></button></div>}
    </div></>;
}

function Cases({ cases, selected, onSelect }) {
    const [query, setQuery] = useState("");

    const filtered = cases.filter((item) =>
        `${getId(item)} ${item.customer_id || ""} ${item.event_type || ""} ${item.payment_method || ""} ${item.recommended_action || ""}`
            .toLowerCase()
            .includes(query.toLowerCase())
    );

    return (
        <>
            <Header
                page={{
                    eyebrow: "CASE MANAGEMENT",
                    title: "Case Explorer",
                    description:
                        "Inspect customer context, AI diagnosis and recovery decisions.",
                    icon: Search
                }}
            />

            <div className="page-content cases-page">
                <div className="panel case-list">
                    <div className="panel-head">
                        <div>
                            <h3>Recovery Cases</h3>
                            <p>{cases.length} cases currently tracked</p>
                        </div>
                    </div>

                    <div className="search-box">
                        <Search size={15} />
                        <input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search cases..."
                        />
                    </div>

                    <div className="case-results">
                        {filtered.length > 0 ? (
                            filtered.map((item) => (
                                <button
                                    className={`case-select ${selected && getId(selected) === getId(item)
                                        ? "selected"
                                        : ""
                                        }`}
                                    key={getId(item)}
                                    onClick={() => onSelect(item)}
                                >
                                    <CreditCard size={19} />

                                    <div>
                                        <b>{getId(item)}</b>
                                        <span>{item.event_type || "Unknown event"}</span>
                                    </div>

                                    <strong>{formatINR(item.amount)}</strong>
                                </button>
                            ))
                        ) : (
                            <div className="empty-state">
                                <Search size={20} />
                                <span>No matching cases found.</span>
                            </div>
                        )}
                    </div>
                </div>

                <div className="panel case-detail">
                    {selected ? (
                        <>
                            <div className="detail-top">
                                <div>
                                    <span>SELECTED CASE</span>
                                    <h2>{getId(selected)}</h2>
                                    <p>{selected.event_type || "Unknown event"}</p>
                                </div>

                                <span className="status">
                                    <i />
                                    {selected.status || "Active"}
                                </span>
                            </div>

                            <div className="detail-grid">
                                <Detail
                                    l="Amount"
                                    v={formatINR(selected.amount)}
                                />

                                <Detail
                                    l="Customer"
                                    v={selected.customer_id || "Unknown"}
                                />

                                <Detail
                                    l="Payment Method"
                                    v={selected.payment_method || "Unknown"}
                                />

                                <Detail
                                    l="Attempts"
                                    v={selected.attempt_count ?? 0}
                                />

                                <Detail
                                    l="Failures"
                                    v={selected.failed_payments ?? 0}
                                />

                                <Detail
                                    l="Probability"
                                    v={pct(selected.recovery_probability)}
                                />
                            </div>

                            <div className="diagnosis">
                                <Bot size={22} />

                                <div>
                                    <span>CASE CONTEXT</span>

                                    <b>
                                        {selected.failure_reason ||
                                            "No failure reason recorded"}
                                    </b>

                                    <p>
                                        Decision context is evaluated from the payment
                                        event, customer history and recovery economics.
                                    </p>
                                </div>
                            </div>
                        </>
                    ) : (
                        <div className="loading-state">
                            Select a case.
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}

function Detail({ l, v }) { return <div className="detail-card"><span>{l}</span><b>{v}</b></div>; }

function Insights({ decision, backendOnline }) {
    const live = decision?.investigator?.live;
    return <><Header page={{ eyebrow: "GEMINI INTELLIGENCE", title: "AI Insights", description: "Explainable intelligence behind every recovery decision.", icon: Lightbulb }} /><div className="page-content"><div className="insight-grid">{[[Bot, "AI Investigation", live ? "Live" : "Available", decision?.investigator?.root_cause || "Gemini grounds diagnosis in payment and customer context."], [Zap, "Decision Intelligence", decision?.strategy?.proposed_action ? actionName(decision.strategy.proposed_action) : "Policy-aware", "Gemini proposes; economics evaluates expected value before authorization."], [ShieldCheck, "Safety Layer", decision?.policy?.decision || "ENFORCED", "Deterministic policy controls bound automated recovery."], [Database, "Evidence Grounding", decision?.investigator?.evidence?.length ? `${decision.investigator.evidence.length} signals` : "Verified", "Decision traces preserve evidence behind interventions."]].map(([I, t, v, p]) => <div className="panel insight" key={t}><I size={25} /><span>{t}</span><b>{v}</b><p>{p}</p></div>)}</div><div className="panel flow-panel"><h3>REVERA Intelligence Flow</h3><p>Detect → Diagnose → Decide → Optimize → Authorize → Execute → Verify</p><div className="flow">{["Detect", "Diagnose", "Decide", "Optimize", "Authorize"].map((x, i) => <React.Fragment key={x}><div><small>0{i + 1}</small><b>{x}</b><span>{["Revenue at risk", "Gemini investigation", "Recovery strategy", "Expected value", "Policy guard"][i]}</span></div>{i < 4 && <ArrowRight />}</React.Fragment>)}</div><div className="integration-line"><Server size={15} /> Backend {backendOnline ? "connected" : "offline"} · Gemini {live ? "live" : "ready"}</div></div></div></>;
}

function Analytics({ data }) {
    const recovered = Number(data?.verified_recovered ?? data?.recovered ?? 0);
    const risk = Number(data?.revenue_at_risk ?? 0);
    const rate = Number(data?.recovery_rate ?? 0);

    return (
        <>
            <Header
                page={{
                    eyebrow: "PERFORMANCE",
                    title: "Analytics",
                    description:
                        "Measure recovery performance, economics and operational outcomes.",
                    icon: BarChart3
                }}
            />

            <div className="page-content">
                <div className="summary-grid">
                    {[
                        ["Recovered Revenue", formatINR(recovered), Coins],
                        ["Recovery Rate", `${(rate * 100).toFixed(1)}%`, Gauge],
                        ["Recovery Attempts", data?.recovery_attempts ?? 0, Workflow],
                        ["Revenue At Risk", formatINR(risk), ShieldCheck]
                    ].map(([title, value, IconComponent]) => (
                        <div className="summary-card panel" key={title}>
                            <IconComponent size={22} />
                            <div>
                                <span>{title}</span>
                                <b>{value}</b>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="analytics-grid">
                    <div className="panel large-chart">
                        <h3>Revenue Recovery</h3>
                        <p>Backend-reported verified recovery</p>

                        <div className="analytics-kpis">
                            <span>
                                Events <b>{data?.events ?? 0}</b>
                            </span>

                            <span>
                                Customers <b>{data?.customers ?? 0}</b>
                            </span>

                            <span>
                                Active Recovery{" "}
                                <b>
                                    {formatINR(data?.active_recovery_value ?? 0)}
                                </b>
                            </span>
                        </div>

                        <div className="recovery-visual">
                            <div className="recovery-visual-value">
                                {formatINR(recovered)}
                            </div>
                            <span>Verified recovered revenue</span>
                        </div>
                    </div>

                    <div className="panel economics">
                        <h3>Recovery Economics</h3>
                        <p>Current backend signals</p>

                        {[
                            ["Verified recovered", formatINR(recovered)],
                            ["At risk", formatINR(risk)],
                            ["Attempts", data?.recovery_attempts ?? 0],
                            [
                                "Average event",
                                formatINR(data?.average_event_value ?? 0)
                            ]
                        ].map(([label, value]) => (
                            <div key={label}>
                                <span>{label}</span>
                                <b>{value}</b>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </>
    );
}

function Benchmark({ data, onRun }) {
    const uplift = Number(data?.relative_uplift || 0) * 100;
    const safety = Number(data?.safety?.policy_compliance || 0) * 100;
    const stopping = Number(data?.safety?.stopping_compliance || 0) * 100;
    const automatic = Number(data?.safety?.automatic_action_rate || 0) * 100;
    const baseline = Number(data?.baseline?.net_recovered ?? data?.baseline?.recovered ?? 0);
    const revera = Number(data?.recoveros?.net_recovered ?? 0);
    const reminder = Number(data?.fixed_reminder?.net_recovered ?? 0);
    return <>
        <Header page={{ eyebrow: "EVALUATION", title: "Benchmark Lab", description: "Measure recovery lift, economics and policy safety across a controlled synthetic cohort.", icon: Lightbulb }} />
        <div className="page-content">
            <div className="panel benchmark-hero polished-benchmark-hero">
                <div>
                    <div className="eyebrow-row"><span>SYNTHETIC BENCHMARK</span><i>Seed {data?.seed || "20260905"}</i></div>
                    <h2>Recovery Intelligence Evaluation</h2>
                    <p>Controlled comparison of REVERA against no-intervention and fixed-strategy baselines. Results are synthetic and not production merchant performance.</p>
                </div>
                <div className="benchmark-hero-actions">
                    {data && <div className={`uplift-chip ${uplift >= 0 ? "positive" : "negative"}`}><strong>{uplift >= 0 ? "+" : ""}{uplift.toFixed(1)}%</strong><span>net uplift</span></div>}
                    <button onClick={onRun}><PlayCircle size={17} />{data ? "Refresh Benchmark" : "Run Benchmark"}</button>
                </div>
            </div>
            {data ? <><div className="benchmark-grid polished-benchmark-grid">
                {[["REVERA", revera, "Net recovered", "active"], ["Baseline", baseline, "No intervention", ""], ["Fixed Reminder", reminder, "Fixed strategy", ""], ["Safety", `${Math.round(safety)}%`, "Policy compliance", "safety"]].map(x => <div className={`panel benchmark-card ${x[3]}`} key={x[0]}><span>{x[0]}</span><b>{typeof x[1] === "number" ? formatINR(x[1]) : x[1]}</b><p>{x[2]}</p></div>)}
            </div>
                <div className="benchmark-detail-grid">
                    <div className="panel controls benchmark-metrics-panel"><div className="section-title"><div><span>PERFORMANCE</span><h3>Recovery Economics</h3></div><strong>{data.cases ?? 0} cases</strong></div><div className="metric-row"><span>Incremental net recovery</span><b>{formatINR(data.incremental_net_recovery)}</b></div><div className="metric-row"><span>Relative uplift</span><b className={uplift >= 0 ? "metric-positive" : "metric-negative"}>{uplift >= 0 ? "+" : ""}{uplift.toFixed(2)}%</b></div><div className="metric-row"><span>REVERA recovery rate</span><b>{(Number(data.recoveros?.recovery_rate || 0) * 100).toFixed(1)}%</b></div></div>
                    <div className="panel controls benchmark-metrics-panel"><div className="section-title"><div><span>GOVERNANCE</span><h3>Safety Controls</h3></div><strong className="safe-label">PASS</strong></div><div className="metric-row"><span>Policy compliance</span><b>{Math.round(safety)}%</b></div><div className="metric-row"><span>Stopping compliance</span><b>{Math.round(stopping)}%</b></div><div className="metric-row"><span>Automatic action rate</span><b>{Math.round(automatic)}%</b></div><div className="metric-row"><span>Policy violations</span><b>{data.safety?.policy_violations ?? 0}</b></div></div>
                </div></> : <div className="panel benchmark-empty"><div className="empty-icon"><PlayCircle size={24} /></div><h3>Benchmark results are ready to load</h3><p>Run the 1,000-case synthetic evaluation to populate recovery lift and safety metrics.</p><button onClick={onRun}><PlayCircle size={16} />Run 1,000-case benchmark</button></div>}
        </div>
    </>;
}

function Audit({ events, onRefresh }) {
    return <><Header page={{ eyebrow: "GOVERNANCE", title: "Audit Trail", description: "Trace every AI decision, policy check and recovery action.", icon: CircleDollarSign }} /><div className="page-content"><div className="audit-actions"><button onClick={onRefresh}><RefreshCw size={15} />Refresh</button><button onClick={() => window.print()}><Download size={15} />Export</button></div><div className="panel audit">{events.length ? events.map((e, i) => <div className="audit-row" key={e.id || `${e.created_at}-${i}`}><div><CheckCircle2 size={18} /></div><section><b>{e.event_type || "EVENT"}</b><p>{e.details || e.message || "Recovery event recorded."}</p><span>{e.actor || "system"}</span></section><time>{e.created_at || ""}</time></div>) : <div className="loading-state">No audit events recorded yet.</div>}</div></div></>;
}

function SettingsPage({ backendOnline }) {
    const [autoRecovery, setAutoRecovery] = useState(true);
    const [auditLogging, setAuditLogging] = useState(true);

    const sections = [
        {
            title: "Recovery Automation",
            rows: [
                {
                    label: "Automated recovery",
                    description: "Allow approved actions to execute automatically.",
                    type: "toggle",
                    value: autoRecovery,
                    onChange: setAutoRecovery
                },
                { label: "Maximum automated recovery", value: "₹50,000" },
                { label: "Maximum attempts", value: "2" },
                { label: "Maximum contacts / 24h", value: "2" }
            ]
        },
        {
            title: "AI Intelligence",
            rows: [
                {
                    label: "Gemini Investigator",
                    description: "Use Gemini for grounded payment diagnosis.",
                    type: "toggle",
                    value: backendOnline,
                    disabled: true
                },
                { label: "Model", value: "Gemini 3.6 Flash" },
                { label: "Structured output", value: "Enabled" }
            ]
        },
        {
            title: "Governance",
            rows: [
                {
                    label: "Audit logging",
                    description: "Record every decision and execution event.",
                    type: "toggle",
                    value: auditLogging,
                    onChange: setAuditLogging
                },
                { label: "Maximum discount", value: "5%" },
                { label: "Human review limit", value: "₹75,000" }
            ]
        },
        {
            title: "Integrations",
            rows: [
                { label: "Razorpay", description: "Connected", value: "Test Mode" },
                { label: "Gemini", description: "Configured", value: "Live when quota is available" },
                { label: "Webhook Gateway", description: "Active", value: "Active" }
            ]
        }
    ];

    return (
        <>
            <Header
                page={{
                    eyebrow: "SYSTEM CONFIGURATION",
                    title: "Settings",
                    description: "Configure REVERA intelligence, automation and governance controls.",
                    icon: Settings
                }}
            />
            <div className="page-content settings">
                {sections.map(section => (
                    <div className="panel setting" key={section.title}>
                        <h3>{section.title}</h3>
                        <p>Configure {section.title.toLowerCase()}.</p>

                        {section.rows.map(row => (
                            <div className="setting-row" key={row.label}>
                                <div>
                                    <b>{row.label}</b>
                                    {row.description && <span>{row.description}</span>}
                                </div>

                                {row.type === "toggle" ? (
                                    <button
                                        className={`toggle ${row.value ? "on" : ""}`}
                                        onClick={() => row.onChange && row.onChange(!row.value)}
                                        disabled={row.disabled}
                                        aria-label={row.label}
                                    >
                                        <i />
                                    </button>
                                ) : (
                                    <strong>{row.value}</strong>
                                )}
                            </div>
                        ))}
                    </div>
                ))}
            </div>
        </>
    );
}

function Footer({ backendOnline }) {
    return <footer><div><b>REVERA</b><span>Intelligent Revenue Recovery System</span></div><section><span><i />Razorpay Test Mode</span><span><i className={backendOnline ? "" : "offline-dot"} />{backendOnline ? "Backend Connected" : "Backend Offline"}</span><time><Clock3 size={16} />{new Date().toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}</time></section></footer>;
}

export default App;
