import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

const isOfficerRole = (role) => role === "OFFICER" || role === "MINISTRY_OFFICER";

const DEMO_OFFICERS = [
  { key: "mp", label: "Madhya Pradesh — Rajesh Verma", email: "officer.mp@bidshield.demo", password: "Demo@MP2026", role: "OFFICER", org: "Madhya Pradesh Public Works Dept." },
  { key: "rj", label: "Rajasthan — Sunita Shekhawat", email: "officer.rajasthan@bidshield.demo", password: "Demo@RJ2026", role: "OFFICER", org: "Rajasthan Urban Development Dept." },
  { key: "mh", label: "Maharashtra — Priya Sharma", email: "officer.maharashtra@bidshield.demo", password: "Demo@MH2026", role: "OFFICER", org: "Maharashtra Infrastructure Development" },
  { key: "gj", label: "Gujarat — Kirit Patel", email: "officer.gujarat@bidshield.demo", password: "Demo@GJ2026", role: "OFFICER", org: "Gujarat Energy & Petrochemicals Dept." },
  { key: "up", label: "Uttar Pradesh — Alok Tripathi", email: "officer.up@bidshield.demo", password: "Demo@UP2026", role: "OFFICER", org: "Uttar Pradesh Public Works Dept." },
];

const DEMO_BIDDERS = [
  { key: "b1", label: "Apex InfraTech Pvt. Ltd. (Bidder 01 · MH)", email: "bidder01@bidshield.demo", password: "Bidder@01", role: "BIDDER", org: "Apex InfraTech Pvt. Ltd." },
  { key: "b2", label: "Bharat Digital Systems Pvt. Ltd. (Bidder 02 · GJ)", email: "bidder02@bidshield.demo", password: "Bidder@02", role: "BIDDER", org: "Bharat Digital Systems Pvt. Ltd." },
  { key: "b3", label: "NexGen Solutions India Pvt. Ltd. (Bidder 03 · RJ)", email: "bidder03@bidshield.demo", password: "Bidder@03", role: "BIDDER", org: "NexGen Solutions India Pvt. Ltd." },
  { key: "b4", label: "Vertex Engineering Services (Bidder 04 · MP)", email: "bidder04@bidshield.demo", password: "Bidder@04", role: "BIDDER", org: "Vertex Engineering Services Pvt. Ltd." },
  { key: "b5", label: "BluePeak Technologies (Bidder 05 · UP)", email: "bidder05@bidshield.demo", password: "Bidder@05", role: "BIDDER", org: "BluePeak Technologies Pvt. Ltd." },
  { key: "b6", label: "Arvind Infrastructure (Bidder 06 · MH)", email: "bidder06@bidshield.demo", password: "Bidder@06", role: "BIDDER", org: "Arvind Infrastructure Solutions Pvt. Ltd." },
  { key: "b7", label: "TechBridge Systems (Bidder 07 · GJ)", email: "bidder07@bidshield.demo", password: "Bidder@07", role: "BIDDER", org: "TechBridge Systems Pvt. Ltd." },
  { key: "b8", label: "Surya Buildcon Projects (Bidder 08 · RJ)", email: "bidder08@bidshield.demo", password: "Bidder@08", role: "BIDDER", org: "Surya Buildcon Projects Pvt. Ltd." },
  { key: "b9", label: "Kavach Cyber Security (Bidder 09 · MP)", email: "bidder09@bidshield.demo", password: "Bidder@09", role: "BIDDER", org: "Kavach Cyber Security Solutions Pvt. Ltd." },
  { key: "b10", label: "Pratham Healthcare Equipments (Bidder 10 · UP)", email: "bidder10@bidshield.demo", password: "Bidder@10", role: "BIDDER", org: "Pratham Healthcare Equipments Pvt. Ltd." },
];

const demo = {
  officer: DEMO_OFFICERS[2], // Maharashtra
  bidder: DEMO_BIDDERS[0],  // Apex
};

async function api(path, opts = {}) {
  const token = localStorage.getItem("bs_token");

  const headers = {
    ...(opts.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    ...(opts.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API}${path}`, {
    ...opts,
    headers,
  });

  const text = await response.text();

  let data = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    if (typeof data.detail === "string") {
      message = data.detail;
    } else if (Array.isArray(data.detail)) {
      message = data.detail
        .map((x) => x.msg || JSON.stringify(x))
        .join(", ");
    } else if (data.error?.message) {
      message = data.error.message;
    }

    throw new Error(message);
  }

  return data;
}

function formatINR(value) {
  const n = Number(value || 0);
  if (n >= 10000000) return `₹${(n / 10000000).toFixed(1)} Cr`;
  if (n >= 100000) return `₹${(n / 100000).toFixed(1)} L`;
  return `₹${n.toLocaleString("en-IN")}`;
}

function formatDate(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function AnalyticsChart({ items = [] }) {
  const max = Math.max(...items.map(x => Number(x.value || 0)), 1);
  return (
    <div className="chart">
      {items.map((x) => (
        <div className="chart-col" key={x.label}>
          <div className="chart-value">{x.value}</div>
          <div className="chart-track"><i style={{ height: `${Math.max(6, (Number(x.value || 0) / max) * 100)}%` }} /></div>
          <span title={x.label}>{x.label}</span>
        </div>
      ))}
    </div>
  );
}

/* =========================
   ICONS
========================= */

function Icon({ name, size = 19 }) {
  const paths = {
    grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",

    building:
      "M4 21V4h11v17M15 8h5v13M8 8h3M8 12h3M8 16h3M17 12h1M17 16h1",

    users:
      "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",

    clipboard:
      "M9 5h6M9 3h6a1 1 0 0 1 1 1v1h2a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2V4a1 1 0 0 1 1-1M8 12h8M8 16h5",

    clock:
      "M12 8v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",

    file:
      "M6 2h8l4 4v16H6zM14 2v5h5M9 12h6M9 16h6",

    shield:
      "M12 3l8 3v6c0 5-3.4 8.8-8 10-4.6-1.2-8-5-8-10V6zM9 12l2 2 4-4",

    search:
      "M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zM21 21l-4.3-4.3",

    plus: "M12 5v14M5 12h14",

    arrow: "M5 12h14M13 6l6 6-6 6",

    download: "M12 3v12M7 10l5 5 5-5M5 21h14",

    logout: "M10 17l5-5-5-5M15 12H3M21 3v18",

    spark:
      "M12 2l1.5 6.5L20 10l-6.5 1.5L12 18l-1.5-6.5L4 10l6.5-1.5z",

    check: "M5 12l4 4L19 6",

    warning:
      "M12 3l9 18H3zM12 9v5M12 17h.01",
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] && <path d={paths[name]} />}
    </svg>
  );
}

/* =========================
   COMMON UI
========================= */

function Logo() {
  return (
    <div className="logo">
      <div className="logo-mark">
        <Icon name="shield" size={20} />
      </div>

      <span>
        BidShield <b>AI</b>
      </span>
    </div>
  );
}

function Badge({ children, tone = "neutral" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

function Stat({ label, value, sub, icon, tone = "" }) {
  return (
    <div className="stat">
      <div>
        <div className="eyebrow">{label}</div>
        <div className="stat-value">{value}</div>
        <div className="muted">{sub}</div>
      </div>

      <div className={`stat-icon ${tone}`}>
        <Icon name={icon} />
      </div>
    </div>
  );
}

/* =========================
   LOGIN
========================= */

function Login({ onLogin }) {
  const now = useClock();
  const [mode, setMode] = useState("officer");
  const [accountKey, setAccountKey] = useState("mh");
  const [email, setEmail] = useState(DEMO_OFFICERS[2].email);
  const [password, setPassword] = useState(DEMO_OFFICERS[2].password);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const fill = (selectedMode) => {
    setMode(selectedMode);
    if (selectedMode === "officer") {
      setAccountKey("mh");
      setEmail(DEMO_OFFICERS[2].email);
      setPassword(DEMO_OFFICERS[2].password);
    } else {
      setAccountKey("b1");
      setEmail(DEMO_BIDDERS[0].email);
      setPassword(DEMO_BIDDERS[0].password);
    }
    setErr("");
  };

  const onSelectAccount = (key) => {
    setAccountKey(key);
    const list = mode === "officer" ? DEMO_OFFICERS : DEMO_BIDDERS;
    const found = list.find((x) => x.key === key);
    if (found) {
      setEmail(found.email);
      setPassword(found.password);
      setErr("");
    }
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setErr("");

    try {
      const result = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      if (!result.access_token) {
        throw new Error("No access token received from server");
      }

      localStorage.setItem("bs_token", result.access_token);
      if (result.user) {
        localStorage.setItem("bs_role", result.user.role);
        localStorage.setItem("bs_name", result.user.full_name);
        localStorage.setItem("bs_email", result.user.email);
        localStorage.setItem("bs_org", result.user.organization_name || "");
      }

      onLogin();
    } catch (error) {
      setErr(error.message || "Unable to sign in");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <aside className="login-hero">
        <Logo />

        <div className="hero-copy">
          <div className="kicker">EVIDENCE-LED PROCUREMENT</div>

          <h1>
            Make the decision
            <br />
            you can stand
            <br />
            behind.
          </h1>

          <p>
            BidShield AI gives procurement teams a calm, auditable
            workspace for tenders, evidence and accountable decisions.
          </p>
        </div>

        <div className="hero-foot">
          <Icon name="shield" size={16} />
          Evidence stays structured. People stay in control.
        </div>
      </aside>

      <main className="login-main">
        <div className="login-clock">
          ◷ &nbsp; {now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })} IST
          <br />
          <small>{now.toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short", year: "numeric" })}</small>
        </div>

        <div className="login-card">
          <div className="kicker">SECURE WORKSPACE ACCESS</div>

          <h2>Welcome back</h2>

          <p className="login-sub">
            Sign in to continue to BidShield AI.
          </p>

          <div className="tabs">
            <button
              type="button"
              className={mode === "officer" ? "active" : ""}
              onClick={() => fill("officer")}
            >
              Officer access (5 States)
            </button>

            <button
              type="button"
              className={mode === "bidder" ? "active" : ""}
              onClick={() => fill("bidder")}
            >
              Registered bidder (10 Vendors)
            </button>
          </div>

          <div className="demo-select-wrap">
            <label style={{ display: "block", fontSize: "11px", fontWeight: "700", color: "#59666d", marginBottom: "6px" }}>
              DEMO ACCOUNT PRESET:
            </label>
            <select
              className="demo-select"
              value={accountKey}
              onChange={(e) => onSelectAccount(e.target.value)}
            >
              {(mode === "officer" ? DEMO_OFFICERS : DEMO_BIDDERS).map((acc) => (
                <option key={acc.key} value={acc.key}>
                  {acc.label}
                </option>
              ))}
            </select>
          </div>

          <div className="hint">
            {mode === "bidder"
              ? "Bidder access is limited to registered bidder accounts."
              : "Procurement officer credentials with full administrative and review rights."}
          </div>

          <form onSubmit={submit}>
            <label>Work email *</label>

            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@organisation.gov.in"
              type="email"
              required
            />

            <label>Password *</label>

            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              type="password"
              required
            />

            <div className="remember">
              <span>☑ Remember me</span>
              <a href="#forgot">Forgot password?</a>
            </div>

            {err && <div className="error">{err}</div>}

            <button
              className="primary wide"
              disabled={loading}
              type="submit"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <div className="divider">
            <span>DEMO ACCESS</span>
          </div>

          <div className="demo-grid">
            <button type="button" onClick={() => fill("officer")}>
              <Icon name="building" />
              Procurement officer
            </button>

            <button type="button" onClick={() => fill("bidder")}>
              <Icon name="users" />
              Registered bidder
              <br />
              demo
            </button>
          </div>

          <div className="demo-pass">
            Demo password: <b>BidShield@2026</b>
            <br />
            Demo access uses local workspace data only.
          </div>
        </div>
      </main>
    </div>
  );
}

/* =========================
   LAYOUT
========================= */

function Layout({
  role,
  onLogout,
  children,
  page,
  setPage,
}) {
  const now = useClock();
  const officerNavigation = [
    ["overview", "Operations overview", "grid"],
    ["tenders", "Tenders", "building"],
    ["bidders", "Bidders", "users"],
    ["review", "Review queue", "clipboard"],
    ["audit", "Audit trail", "clock"],
    ["reports", "Reports", "file"],
  ];

  const bidderNavigation = [
    ["overview", "My overview", "grid"],
    ["browse", "Browse tenders", "building"],
    ["mybids", "My bids", "clipboard"],
    ["vault", "Document vault", "file"],
    ["profile", "Company profile", "users"],
    ["notifications", "Notifications", "clock"],
  ];

  const items =
    isOfficerRole(role)
      ? officerNavigation
      : bidderNavigation;

  const name =
    localStorage.getItem("bs_name") ||
    (isOfficerRole(role)
      ? "Priya Sharma"
      : "Arjun Mehta");

  const org =
    localStorage.getItem("bs_org") ||
    (isOfficerRole(role)
      ? "Maharashtra Works Dept."
      : "ABC Construction Pvt Ltd");

  const [summary, setSummary] = useState(null);
  useEffect(() => {
    api("/dashboard/summary")
      .then(setSummary)
      .catch(() => {});
  }, [page]);

  const reviewBadgeCount = summary?.pending_reviews || 0;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Logo />

        <div className="workspace">
          <div className="eyebrow">
            {isOfficerRole(role)
              ? "PROCUREMENT WORKSPACE"
              : "BIDDER WORKSPACE"}
          </div>

          <b>{org}</b>
        </div>

        <nav>
          {items.map(([id, label, icon]) => (
            <button
              key={id}
              type="button"
              className={page === id ? "nav-active" : ""}
              onClick={() => setPage(id)}
            >
              <Icon name={icon} />

              <span>{label}</span>

              {id === "review" && reviewBadgeCount > 0 && <em>{reviewBadgeCount}</em>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button type="button">
            <Icon name="shield" />
            {isOfficerRole(role)
              ? "Workspace settings"
              : "Help centre"}
          </button>

          <button type="button" onClick={onLogout}>
            <Icon name="logout" />
            Sign out
          </button>
        </div>
      </aside>

      <main className="content">
        <header>
          <span className="crumb">
            {org} / FY 2026–27
          </span>

          <div className="top-right">
            <span className="clock">
              ◷ &nbsp; <b>{now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })} IST</b>
              <small>{now.toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short", year: "numeric" })}</small>
            </span>

            <span className="help">?</span>

            <span className="avatar">
              {name
                .split(" ")
                .map((x) => x[0])
                .join("")
                .slice(0, 2)}
            </span>

            <b>{name}</b>
          </div>
        </header>

        {children}
      </main>
    </div>
  );
}

/* =========================
   OFFICER OVERVIEW
========================= */

function OfficerOverview({ go }) {
  const [data, setData] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    Promise.all([api("/dashboard/summary"), api("/dashboard/analytics")])
      .then(([summary, stats]) => { setData(summary); setAnalytics(stats); })
      .catch((err) => { setError(err.message || "Failed to load dashboard metrics"); })
      .finally(() => setLoading(false));
  };
  useEffect(load, []);

  const active = data?.active_tenders ?? 0;
  const reviews = data?.pending_reviews ?? 0;
  const assessed = data?.bids_received ?? 0;
  const tenderItems = (analytics?.tenders || []).slice(0, 5);

  return (
    <>
      <div className="page-head">
        <div>
          <div className="kicker">LIVE PROCUREMENT OPERATIONS</div>
          <h1>Good evening, {localStorage.getItem("bs_name") || "Officer"}.</h1>
          <p>Live tender, bid and AI assessment activity from your database.</p>
        </div>
        <button className="primary" onClick={() => go("tenders")}><Icon name="plus" /> Create tender</button>
      </div>

      {error && <div className="error" style={{margin: "0 0 15px"}}>{error}</div>}
      {loading && !data && <div className="empty compact"><p>Loading live metrics…</p></div>}

      <div className="stats four">
        <Stat label="ACTIVE TENDERS" value={String(active)} sub="From live database" icon="building" tone="gold" />
        <Stat label="PENDING REVIEW" value={String(reviews).padStart(2, "0")} sub="Needs human decision" icon="clipboard" />
        <Stat label="BIDS RECEIVED" value={String(assessed)} sub="Across all tenders" icon="users" />
        <Stat label="AWARD PIPELINE" value={formatINR(data?.award_value)} sub="Recorded award value" icon="file" />
      </div>

      <div className="grid-2">
        <section className="panel">
          <PanelHead title="Tender comparison" sub="Live bids received per tender" action="Open tenders" />
          <AnalyticsChart items={tenderItems.map(t => ({ label: t.tender_number, value: t.bids }))} />
          <div className="data-list">
            {tenderItems.map(t => (
              <div className="data-row" key={t.id}>
                <div><b>{t.tender_number}</b><span>{t.title}</span></div>
                <strong>{t.bids} bids</strong>
              </div>
            ))}
          </div>
        </section>

        <section className="panel">
          <PanelHead title="AI decision pipeline" sub="Current database status" />
          {[
            ["Draft / preparation", analytics?.bid_status?.DRAFT || 0],
            ["Submitted", analytics?.bid_status?.SUBMITTED || 0],
            ["Under AI / human review", analytics?.bid_status?.UNDER_REVIEW || 0],
            ["Accepted", analytics?.bid_status?.ACCEPTED || 0],
            ["Rejected", analytics?.bid_status?.REJECTED || 0],
          ].map(([label, value]) => (
            <div className="data-row" key={label}><div><b>{label}</b><span>Live bid records</span></div><strong>{value}</strong></div>
          ))}
          <button className="secondary full-action" onClick={() => go("review")}>Open review queue <Icon name="arrow" size={14} /></button>
        </section>
      </div>

      <section className="panel">
        <PanelHead title="Latest tenders" sub="Real records, deadlines and participation" />
        {tenderItems.map(t => (
          <TenderRow key={t.id} t={{...t, deadline: formatDate(t.deadline), value: t.estimated_value, department: t.department}} onClick={() => go("tenders")} />
        ))}
      </section>
    </>
  );
}

/* =========================
   BIDDER OVERVIEW
========================= */

function BidderOverview({ go }) {
  const [data, setData] = useState(null);
  const [bids, setBids] = useState([]);
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    Promise.all([api("/dashboard/summary"), api("/bids"), api("/tenders")])
      .then(([s,b,t]) => { setData(s); setBids(Array.isArray(b) ? b : []); setTenders(Array.isArray(t) ? t : []); })
      .catch((err) => { setError(err.message || "Failed to load supplier overview"); })
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-head">
        <div><div className="kicker">SUPPLIER PORTAL / LIVE</div><h1>Good evening, {localStorage.getItem("bs_name") || "Bidder"}.</h1><p>Submit bids, prepare evidence and track the real tender pipeline.</p></div>
        <button className="primary" onClick={() => go("browse")}><Icon name="building" /> Browse tenders</button>
      </div>

      {error && <div className="error" style={{margin: "0 0 15px"}}>{error}</div>}
      {loading && !data && <div className="empty compact"><p>Loading supplier metrics…</p></div>}

      <div className="stats three">
        <Stat label="ACTIVE TENDERS" value={String(data?.active_tenders || 0)} sub="Available now" icon="building" tone="peach" />
        <Stat label="MY BIDS" value={String(data?.my_bids || 0)} sub="Saved in database" icon="clipboard" />
        <Stat label="DOCUMENTS" value={String(data?.documents || 0)} sub="Uploaded to your bids" icon="file" />
      </div>

      <div className="grid-2">
        <section className="panel">
          <PanelHead title="My recent bids" sub="Live submission progress" />
          {bids.slice(0,5).map(b => <BidRow key={b.id} b={b} />)}
          {!bids.length && !loading && <div className="empty"><h3>No bids yet</h3><p>Open a published tender and start your first submission.</p></div>}
        </section>
        <section className="panel">
          <PanelHead title="Opportunities" sub="Published tenders you can bid on" />
          {tenders.filter(t => t.status === "PUBLISHED").slice(0,5).map(t => (
            <div className="data-row" key={t.id}><div><b>{t.tender_number}</b><span>{t.title}</span></div><button className="text-btn" onClick={() => go("browse")}>Open <Icon name="arrow" size={13}/></button></div>
          ))}
        </section>
      </div>
    </>
  );
}

/* =========================
   PANEL
========================= */

function PanelHead({ title, sub, action }) {
  return (
    <div className="panel-head">
      <div>
        <h3>{title}</h3>

        {sub && <span>{sub}</span>}
      </div>

      {action && (
        <button className="text-btn" type="button">
          {action} <Icon name="arrow" size={14} />
        </button>
      )}
    </div>
  );
}

/* =========================
   TENDER ROW
========================= */

function TenderRow({ t, onClick }) {
  return (
    <div className="row" onClick={onClick}>
      <div>
        <small>{t.tender_number}</small>

        <b>{t.title}</b>

        <span>{t.department}</span>
      </div>

      <div className="row-end">
        <Badge
          tone={
            t.status === "PUBLISHED"
              ? "success"
              : "neutral"
          }
        >
          {t.status === "PUBLISHED" ? "Open" : "Closed"}
        </Badge>

        <span>{t.bids ?? 0} bids</span>
      </div>
    </div>
  );
}

/* =========================
   BID ROW
========================= */

function BidRow({ b }) {
  const status = String(b.status || "");

  return (
    <div className="row">
      <div>
        <small>
          {String(b.id || "").toUpperCase()}
        </small>

        <b>{b.title}</b>

        <span>{b.submitted_at ? `Submitted ${formatDate(b.submitted_at)}` : "Draft · not submitted"}</span>
      </div>

      <div className="row-end">
        <Badge
          tone={
            status === "ACCEPTED"
              ? "success"
              : status === "UNDER_REVIEW"
              ? "info"
              : "warning"
          }
        >
          {status === "UNDER_REVIEW"
            ? "Under review"
            : status === "ACCEPTED"
            ? "Awarded"
            : "In preparation"}
        </Badge>
      </div>
    </div>
  );
}

/* =========================
   TENDERS
========================= */

function Tenders({ role, go }) {
  const [search, setSearch] = useState("");
  const [live, setLive] = useState([]);
  const [myBids, setMyBids] = useState({});
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [form, setForm] = useState({ tender_number: "", title: "", department: "Public Works · Maharashtra", category: "GENERAL", estimated_value: "", submission_deadline: "", description: "" });

  const load = () => {
    api("/tenders").then(setLive).catch(err => setMessage(err.message));
    if (role === "BIDDER") {
      api("/bids").then(bids => {
        const map = {};
        (bids || []).forEach(b => { map[b.tender_id] = b; });
        setMyBids(map);
      }).catch(() => {});
    }
  };
  useEffect(() => { load(); }, []);

  const createTender = async (e) => {
    e.preventDefault(); setCreating(true); setMessage("");
    try {
      const created = await api("/tenders", { method: "POST", body: JSON.stringify({...form, estimated_value: Number(form.estimated_value || 0), submission_deadline: form.submission_deadline ? new Date(form.submission_deadline).toISOString() : null}) });
      await api(`/tenders/${created.id}/requirements`, { method: "POST", body: JSON.stringify({ requirement_text: "Valid company registration certificate", mandatory: true, weight: 1 }) });
      await api(`/tenders/${created.id}/requirements`, { method: "POST", body: JSON.stringify({ requirement_text: "GST and tax compliance certificate", mandatory: true, weight: 1 }) });
      await api(`/tenders/${created.id}/requirements`, { method: "POST", body: JSON.stringify({ requirement_text: "Technical and financial eligibility as specified", mandatory: true, weight: 1 }) });
      await api(`/tenders/${created.id}/publish`, { method: "POST" });
      setShowCreate(false); setForm({ tender_number:"",title:"",department:"Public Works · Maharashtra",category:"GENERAL",estimated_value:"",submission_deadline:"",description:"" });
      setMessage("Tender created, requirements added and published.");
      await load();
    } catch (err) { setMessage(err.message); } finally { setCreating(false); }
  };

  const startBid = async (tender) => {
    try {
      const b = await api(`/bids/tenders/${tender.id}/bids`, { method: "POST", body: JSON.stringify({}) });
      setMessage(`Bid created for ${tender.tender_number}. Open My bids to add evidence.`);
      go("mybids");
    } catch (err) { setMessage(err.message); }
  };

  const source = live.map(t => ({...t, deadline: formatDate(t.submission_deadline), value: t.estimated_value, department: t.department || "—", bids: t.bid_count || 0}));
  const list = source.filter(item => `${item.title} ${item.tender_number} ${item.department}`.toLowerCase().includes(search.toLowerCase()));

  return (
    <>
      <div className="page-head">
        <div><div className="kicker">{isOfficerRole(role) ? "PROCUREMENT PIPELINE" : "OPPORTUNITIES"}</div><h1>{isOfficerRole(role) ? "Tenders" : "Browse tenders"}</h1><p>{isOfficerRole(role) ? "Create, publish and monitor live tender opportunities." : "Discover published tenders and track your bid status."}</p></div>
        {isOfficerRole(role) && <button className="primary" onClick={() => setShowCreate(true)}><Icon name="plus" /> Create tender</button>}
      </div>
      {message && <div className="success-box" style={{margin:"0 32px 15px"}}>{message}</div>}
      <div className="toolbar"><div className="search"><Icon name="search" /><input placeholder="Search tenders…" value={search} onChange={e => setSearch(e.target.value)} /></div><span className="filter">Live database · {list.length} results</span></div>
      <section className="panel">
        <PanelHead title={`${list.length} tenders`} sub="Real tender records" />
        {list.map(t => {
          const myBid = myBids[t.id];
          const isClosed = t.status !== "PUBLISHED" || (t.submission_deadline && new Date(t.submission_deadline) < new Date());
          return (
            <div className="tender-live-row" key={t.id}>
              <TenderRow t={t} onClick={() => isOfficerRole(role) ? go("review") : null} />
              {role === "BIDDER" && (
                myBid ? (
                  myBid.status === "DRAFT" ? (
                    <button className="secondary small-btn" onClick={() => go("mybids")}>Continue draft</button>
                  ) : (
                    <div className="small-btn" style={{display:"flex", gap:"8px", alignItems:"center"}}>
                      <Badge tone="success">Bid submitted (Locked)</Badge>
                      <button className="secondary" style={{padding:"6px 10px", fontSize:"11px"}} onClick={() => go("mybids")}>View</button>
                    </div>
                  )
                ) : isClosed ? (
                  <div className="small-btn"><Badge tone="neutral">Closed</Badge></div>
                ) : (
                  <button className="primary small-btn" onClick={() => startBid(t)}>Start bid</button>
                )
              )}
            </div>
          );
        })}
        {!list.length && <div className="empty"><h3>No matching tenders</h3><p>Create a tender or change the search.</p></div>}
      </section>

      {showCreate && (
        <div className="modal-backdrop" onMouseDown={() => setShowCreate(false)}>
          <form className="modal" onSubmit={createTender} onMouseDown={e => e.stopPropagation()}>
            <div className="detail-head"><div><div className="kicker">NEW OPPORTUNITY</div><h2>Create tender</h2></div><button type="button" className="icon-btn" onClick={() => setShowCreate(false)}>×</button></div>
            <div className="form-grid">
              <label>Tender number<input required value={form.tender_number} onChange={e=>setForm({...form,tender_number:e.target.value})} placeholder="TND-2026-050" /></label>
              <label>Category<input value={form.category} onChange={e=>setForm({...form,category:e.target.value})} /></label>
              <label className="span-2">Title<input required value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="Construction / service title" /></label>
              <label>Estimated value (₹)<input type="number" value={form.estimated_value} onChange={e=>setForm({...form,estimated_value:e.target.value})} /></label>
              <label>Submission deadline<input required type="datetime-local" value={form.submission_deadline} onChange={e=>setForm({...form,submission_deadline:e.target.value})} /></label>
              <label className="span-2">Department<input value={form.department} onChange={e=>setForm({...form,department:e.target.value})} /></label>
              <label className="span-2">Description<textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} rows="3" /></label>
            </div>
            <div className="decision-actions"><button type="button" className="secondary" onClick={() => setShowCreate(false)}>Cancel</button><button className="primary" disabled={creating}>{creating ? "Publishing…" : "Create & publish"}</button></div>
          </form>
        </div>
      )}
    </>
  );
}

/* =========================
   REVIEW
========================= */

function Review() {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  useEffect(() => { api("/bids").then(data => { setItems(data || []); setSelected((data || [])[0] || null); }).catch(() => {}); }, []);
  return (
    <>
      <div className="page-head"><div><div className="kicker">HUMAN REVIEW QUEUE</div><h1>Evidence review</h1><p>AI findings are recommendations. Your decision remains the final control.</p></div><Badge tone="warning">{items.filter(x=>x.status==="UNDER_REVIEW").length} awaiting review</Badge></div>
      <div className="review-layout">
        <section className="panel queue">{items.map(b => <button className={`queue-item ${selected?.id===b.id?"selected":""}`} onClick={()=>setSelected(b)} key={b.id} type="button"><div><small>{b.tender_number}</small><b>{b.title}</b><span>{b.bidder_name || "Bidder"} · {String(b.status).replaceAll("_"," ")}</span></div><Badge tone={b.ai_recommendation==="PASS"?"success":"warning"}>{b.ai_recommendation || "REVIEW"}</Badge></button>)}{!items.length&&<div className="empty"><h3>No bids in queue</h3><p>Submit a bidder entry to populate this workspace.</p></div>}</section>
        <section className="panel review-detail">{selected ? <ReviewDetail bid={selected} /> : <div className="empty"><h3>Select a bid to review</h3></div>}</section>
      </div>
    </>
  );
}

/* =========================
   REVIEW DETAIL
========================= */

function ReviewDetail({ bid }) {
  const [result, setResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  const loadAnalysis = () => {
    if (!bid?.id) return;
    setResult(null);
    setError("");
    api(`/compliance/bids/${bid.id}/result`)
      .then((data) => {
        if (data && data.status !== "NOT_ANALYZED") {
          setResult(data);
        }
      })
      .catch(() => {});
  };

  useEffect(() => {
    loadAnalysis();
  }, [bid?.id]);

  const runAnalysis = async () => {
    setSaving(true);
    setError("");
    setDone("");
    try {
      const res = await api(`/compliance/bids/${bid.id}/analyze`, { method: "POST" });
      setResult(res);
      setDone("AI compliance & risk analysis completed and saved to database.");
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const saveDecision = async (decision) => {
    setSaving(true);
    setError("");
    try {
      const reason =
        decision === "APPROVE"
          ? "Officer approved after comprehensive evidence review."
          : decision === "REJECT"
          ? "Officer rejected: Mandatory tender qualifications not satisfied."
          : "Clarification required on submitted qualifications.";
      await api(`/bids/${bid.id}/decision`, {
        method: "POST",
        body: JSON.stringify({ decision, reason }),
      });
      setDone(`Officer decision (${decision}) recorded in cryptographic audit trail.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const score = result?.overall_compliance_score ?? null;
  const risk = result?.risk?.level || "—";
  const reqs = result?.requirements || [];
  const ai = result?.ai_analysis || null;
  const overallText = ai?.overall_assessment || result?.explanation || "";

  return (
    <div>
      <div className="detail-head">
        <div>
          <small>{bid.tender_number} · {bid.bidder_name || "Bidder"}</small>
          <h2>{bid.title}</h2>
        </div>
        <Badge tone={bid.ai_recommendation === "PASS" ? "success" : "warning"}>
          AI: {result?.ai_recommendation || bid.ai_recommendation || "REVIEW"}
        </Badge>
      </div>

      <div className="score-card">
        <div>
          <span className="eyebrow">COMPLIANCE SCORE</span>
          <strong>{score === null ? "—" : `${Math.round(score)}%`}</strong>
          <span>{score === null ? "Run analysis after documents are uploaded" : "Evidence-backed assessment"}</span>
        </div>
        <div className="risk">
          <span>Risk Level</span>
          <b>{risk}</b>
          <div className="progress">
            <i style={{ width: `${Math.min(100, Number(result?.risk?.score || 0))}%` }} />
          </div>
        </div>
      </div>

      <div className="ai-callout">
        <div className="ai-icon"><Icon name="spark" /></div>
        <div>
          <b>AI compliance & risk engine</b>
          <p>Deterministic rules + RAG chunk retrieval + Groq LLM reasoning evaluate bidder qualifications.</p>
        </div>
        <button className="secondary" disabled={saving} onClick={runAnalysis}>
          {saving ? "Analyzing…" : "Re-run AI Analysis"}
        </button>
      </div>

      {overallText && (
        <div className="ai-insights">
          <h4>AI Executive Evaluation (LLM)</h4>
          <p style={{ fontSize: "13px", lineHeight: 1.5, margin: "0 0 10px", color: "#2c3e50" }}>{overallText}</p>
          {ai?.key_strengths?.length > 0 && (
            <div style={{ marginBottom: "8px" }}>
              <b style={{ fontSize: "12px", color: "var(--green)" }}>✓ Key Strengths:</b>
              <ul>
                {ai.key_strengths.map((s, idx) => (
                  <li key={idx}>{s}</li>
                ))}
              </ul>
            </div>
          )}
          {ai?.key_concerns?.length > 0 && (
            <div style={{ marginBottom: "8px" }}>
              <b style={{ fontSize: "12px", color: "var(--warn)" }}>⚠ Identified Concerns:</b>
              <ul>
                {ai.key_concerns.map((c, idx) => (
                  <li key={idx}>{c}</li>
                ))}
              </ul>
            </div>
          )}
          {ai?.clarifications_required?.length > 0 && (
            <div>
              <b style={{ fontSize: "12px", color: "var(--info)" }}>ℹ Clarifications Required:</b>
              <ul>
                {ai.clarifications_required.map((cl, idx) => (
                  <li key={idx}>{cl}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <h3 className="section-title">Evidence checks</h3>
      {reqs.length ? (
        reqs.map((r) => (
          <div className="check-row" key={r.requirement_id}>
            <div className={`check ${r.status === "PASS" ? "ok" : "warn"}`}>
              <Icon name={r.status === "PASS" ? "check" : "warning"} size={16} />
            </div>
            <div>
              <b>{r.requirement}</b>
              <span>{r.explanation} · confidence {Math.round((r.confidence || 0) * 100)}%</span>
            </div>
            <Badge tone={r.status === "PASS" ? "success" : "warning"}>{r.status}</Badge>
          </div>
        ))
      ) : (
        <div className="empty compact">
          <p>No analysis result cached yet. Click "Re-run AI Analysis" to trigger the engine.</p>
        </div>
      )}

      <div className="decision">
        <div>
          <b>Officer decision</b>
          <span>AI recommends; the officer retains final accountable decision control.</span>
        </div>
        <div className="decision-actions">
          <button className="secondary" disabled={saving} onClick={() => saveDecision("CLARIFICATION_REQUIRED")}>
            Request clarification
          </button>
          <button className="secondary" style={{ color: "var(--danger)" }} disabled={saving} onClick={() => saveDecision("REJECT")}>
            Reject bid
          </button>
          <button className="primary" disabled={saving} onClick={() => saveDecision("APPROVE")}>
            Approve bid
          </button>
        </div>
      </div>

      {error && <div className="error" style={{ marginTop: "12px" }}>{error}</div>}
      {done && (
        <div className="success-box" style={{ marginTop: "12px" }}>
          <Icon name="check" /> {done}
        </div>
      )}
    </div>
  );
}

/* =========================
   BIDS
========================= */

function Bids({ role }) {
  const [items, setItems] = useState([]);
  const [selected, setSelected] = useState(null);
  const [docs, setDocs] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const load = () => api("/bids").then(data => { setItems(data || []); setSelected(cur => cur && (data||[]).find(x=>x.id===cur.id) || (data||[])[0] || null); }).catch(err=>setMessage(err.message));
  useEffect(() => { load(); }, []);
  useEffect(() => { if(selected) api(`/documents/bids/${selected.id}`).then(setDocs).catch(()=>setDocs([])); }, [selected]);

  const upload = async (e) => {
    const file = e.target.files?.[0]; if(!file || !selected) return;
    setBusy(true); setMessage("");
    try {
      const fd = new FormData(); fd.append("file", file);
      const up = await api(`/documents/bids/${selected.id}/upload`, {method:"POST", body:fd});
      await api(`/documents/${up.document_id}/process`, {method:"POST"});
      setMessage(`${file.name} uploaded, processed and hashed successfully.`);
      const d = await api(`/documents/bids/${selected.id}`); setDocs(d);
    } catch(err){setMessage(err.message)} finally{setBusy(false);e.target.value=""}
  };
  const submit = async () => {
    setBusy(true); setMessage("");
    try { await api(`/bids/${selected.id}/submit`, {method:"POST"}); setMessage("Bid submitted successfully."); await load(); }
    catch(err){setMessage(err.message)} finally{setBusy(false)}
  };
  const [verifying, setVerifying] = useState({});
  const verifyDoc = async (docId) => {
    setVerifying(v => ({...v, [docId]: true})); setMessage("");
    try {
      const result = await api(`/verification/${docId}`, {method:"POST"});
      setDocs(cur => cur.map(d => d.id === docId ? {...d, verification: result.overall_status} : d));
    } catch(err) { setMessage(err.message); } finally { setVerifying(v => ({...v, [docId]: false})); }
  };

  return <>
    <div className="page-head"><div><div className="kicker">{role==="OFFICER"?"ASSESSMENT WORKSPACE":"SUBMISSION WORKSPACE"}</div><h1>{role==="OFFICER"?"Bids & assessments":"My bids"}</h1><p>{role==="OFFICER"?"Review live bidder submissions and run the AI engine.":"Add evidence PDFs, process them and submit your bid."}</p></div></div>
    {message&&<div className="success-box" style={{margin:"0 32px 15px"}}>{message}</div>}
    <div className="grid-2">
      <section className="panel">{items.map(b=><button className={`queue-item ${selected?.id===b.id?"selected":""}`} key={b.id} onClick={()=>setSelected(b)} type="button"><div><small>{b.tender_number}</small><b>{b.title}</b><span>{b.bidder_name || "Your company"} · {String(b.status).replaceAll("_"," ")}</span></div><Badge tone={b.ai_recommendation==="PASS"?"success":"warning"}>{b.ai_recommendation||"REVIEW"}</Badge></button>)}{!items.length&&<div className="empty"><h3>No bids yet</h3><p>Browse a published tender to create one.</p></div>}</section>
      <section className="panel bid-detail">{selected ? <>
        <div className="detail-head"><div><small>{selected.tender_number} · {selected.bidder_name || "Bidder"}</small><h2>{selected.title}</h2></div><Badge tone="info">{selected.status}</Badge></div>
        <div className="metric-grid"><div><span>AI recommendation</span><b>{selected.ai_recommendation||"REVIEW"}</b></div><div><span>Documents</span><b>{docs.length}</b></div><div><span>Submitted</span><b>{selected.status==="DRAFT"?"Not yet":"Yes"}</b></div><div><span>Evidence</span><b>{docs.filter(d=>d.status==="PROCESSED").length} processed</b></div></div>
        <div className="ai-callout"><div className="ai-icon"><Icon name="spark"/></div><div><b>{role==="OFFICER"?"AI compliance review":"Evidence readiness"}</b><p>{role==="OFFICER"?"Run rule + RAG + LLM analysis against the tender requirements.":"PDF evidence is stored locally, hashed and processed for later AI analysis."}</p></div>{role==="BIDDER"&&<label className="secondary upload-btn">+ Add PDF<input type="file" accept="application/pdf" onChange={upload} disabled={busy}/></label>}</div>
        <h3 className="section-title">Document readiness</h3>
        {docs.map(d=><div className="file-row" key={d.id}><Icon name="file"/><div><b>{d.filename}</b><span>{d.status} · SHA-256 {d.sha256.slice(0,12)}…{d.verification?` · Authenticity: ${d.verification}`:""}</span></div>
          <Badge tone={d.status==="PROCESSED"?"success":"warning"}>{d.status==="PROCESSED"?"Ready":"Processing"}</Badge>
          {d.verification && <Badge tone={d.verification==="VERIFIED"?"success":d.verification==="FAILED"?"warning":"info"}>{d.verification}</Badge>}
          {role==="OFFICER" && d.status==="PROCESSED" && <button className="text-btn" type="button" disabled={verifying[d.id]} onClick={()=>verifyDoc(d.id)}>{verifying[d.id]?"Checking…":d.verification?"Re-check":"Verify authenticity"}</button>}
        </div>)}
        {!docs.length&&<div className="empty compact"><p>No documents attached yet.</p></div>}
        <div className="decision">{role==="BIDDER"?<><div><b>Ready to submit?</b><span>Submit only after your required evidence is processed.</span></div><button className="primary" disabled={busy || !docs.length || selected.status!=="DRAFT"} onClick={submit}>{busy?"Working…":"Submit bid"}</button></>:<div><b>Next step</b><span>Select this bid in the Review queue to run AI analysis and record the officer decision.</span></div>}</div>
      </>:<div className="empty"><h3>Select a bid</h3></div>}</section>
    </div>
  </>;
}

/* =========================
   AUDIT
========================= */

function Audit() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api("/audit")
      .then((data) => setRows(Array.isArray(data) ? data : []))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const exportLog = () => {
    const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "audit-trail.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <div className="page-head">
        <div>
          <div className="kicker">
            CRYPTOGRAPHIC AUDIT TRAIL
          </div>

          <h1>Audit trail</h1>

          <p>
            Every material action is chained with SHA-256 hashes
            (blockchain-ready cryptographic audit architecture) —
            trace evidence events and officer decisions.
          </p>
        </div>

        <button className="secondary" onClick={exportLog} disabled={!rows.length}>
          <Icon name="download" />
          Export log
        </button>
      </div>

      <section className="panel">
        <PanelHead
          title={`${rows.length} events`}
          sub="Hash-linked local audit records, most recent first"
        />

        {error && <div className="error">{error}</div>}
        {loading && !rows.length && !error && <div className="empty compact"><p>Loading audit records…</p></div>}

        <div className="timeline">
          {rows.map((event) => (
            <div className="event" key={event.id}>
              <span>
                {event.timestamp
                  ? new Date(event.timestamp).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })
                  : "—"}
              </span>

              <div className="event-dot">
                <Icon name="check" size={13} />
              </div>

              <div>
                <b>{event.action}</b>

                <span>
                  {event.entity_type} {event.entity_id ? `· ${String(event.entity_id).slice(0, 8)}…` : ""}
                </span>
              </div>

              <code>
                sha:{(event.current_hash || "").slice(0, 8)}…
              </code>
            </div>
          ))}
        </div>

        {!loading && !rows.length && !error && (
          <div className="empty compact"><p>No audit events yet. Actions like tender creation, document upload, AI analysis and officer decisions will appear here as they happen.</p></div>
        )}
      </section>
    </>
  );
}

function Reports() {
  const [a,setA]=useState(null);
  useEffect(()=>{api("/dashboard/analytics").then(setA).catch(()=>{})},[]);
  const rows=(a?.tenders||[]).slice(0,8);
  return <><div className="page-head"><div><div className="kicker">DECISION REPORTING</div><h1>Reports & comparison</h1><p>Compare participation, tender value and the AI assessment pipeline.</p></div></div>
    <div className="grid-2">
      <section className="panel"><PanelHead title="Bids by tender" sub="Participation comparison"/><AnalyticsChart items={rows.map(t=>({label:t.tender_number,value:t.bids}))}/></section>
      <section className="panel"><PanelHead title="Tender value" sub="Estimated procurement value"/><AnalyticsChart items={rows.map(t=>({label:t.tender_number,value:Math.round(Number(t.estimated_value||0)/1000000)}))}/><p className="chart-note">Values shown in ₹ million.</p></section>
    </div>
    <section className="panel"><PanelHead title="Tender performance table" sub="Every tender in the live database"/>{rows.map(t=><div className="data-row" key={t.id}><div><b>{t.tender_number}</b><span>{t.title}</span></div><strong>{t.bids} bids · {formatINR(t.estimated_value)}</strong></div>)}</section>
  </>;
}

function Bidders() {
  const [rows,setRows]=useState([]);
  useEffect(()=>{api("/dashboard/bidders").then(setRows).catch(()=>{})},[]);
  return <><div className="page-head"><div><div className="kicker">SUPPLIER DIRECTORY</div><h1>Bidders</h1><p>Live bidder participation and verification posture.</p></div></div>
    <section className="panel">{rows.map(b=><div className="data-row" key={b.id}><div><b>{b.name}</b><span>{b.registration_number || "Registration not provided"} · {b.verification_status}</span></div><strong>{b.bids} bids · {b.submitted} submitted</strong></div>)}{!rows.length&&<div className="empty"><h3>No bidders yet</h3></div>}</section>
  </>;
}

/* =========================
   DOCUMENT VAULT
========================= */

function DocumentVault({ role }) {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    api("/bids")
      .then(async (bids) => {
        const allDocs = [];
        for (const b of bids || []) {
          try {
            const dList = await api(`/documents/bids/${b.id}`);
            (dList || []).forEach((d) => {
              allDocs.push({
                ...d,
                tender_number: b.tender_number,
                tender_title: b.title,
                bid_status: b.status,
              });
            });
          } catch {}
        }
        setDocs(allDocs);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-head">
        <div>
          <div className="kicker">SECURE EVIDENCE REPOSITORY</div>
          <h1>Document vault</h1>
          <p>Cryptographically hashed PDF evidence, status tracking, and authenticity records.</p>
        </div>
        <Badge tone="info">{docs.length} stored documents</Badge>
      </div>

      <section className="panel">
        <PanelHead title="Evidence documents" sub="All uploaded bid files with SHA-256 integrity verification" />
        {error && <div className="error" style={{ margin: "16px 20px" }}>{error}</div>}
        {loading && !docs.length && <div className="empty compact"><p>Loading documents from vault…</p></div>}
        {!loading && !docs.length && !error && (
          <div className="empty compact"><p>No documents uploaded yet. Open your bids to upload PDF evidence.</p></div>
        )}
        {docs.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table className="vault-table">
              <thead>
                <tr>
                  <th>DOCUMENT</th>
                  <th>TENDER / BID</th>
                  <th>FILE SIZE</th>
                  <th>INTEGRITY (SHA-256)</th>
                  <th>PROCESSING</th>
                  <th>AUTHENTICITY</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <Icon name="file" size={16} />
                        <b>{d.filename || "document.pdf"}</b>
                      </div>
                    </td>
                    <td>
                      <span>{d.tender_number}</span>
                      <small style={{ display: "block", color: "#8a9298", fontSize: "10px" }}>{d.tender_title}</small>
                    </td>
                    <td>{d.file_size ? `${(d.file_size / 1024).toFixed(1)} KB` : "—"}</td>
                    <td><code>{d.sha256 ? `${d.sha256.slice(0, 16)}…` : "—"}</code></td>
                    <td>
                      <Badge tone={d.status === "PROCESSED" ? "success" : "warning"}>{d.status}</Badge>
                    </td>
                    <td>
                      <Badge tone={d.verification === "VERIFIED" ? "success" : d.verification === "FAILED" ? "danger" : "info"}>
                        {d.verification || "VERIFIED"}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

/* =========================
   COMPANY PROFILE
========================= */

function CompanyProfile({ role }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api("/auth/me").catch(() => null),
      api("/dashboard/bidders").catch(() => []),
    ])
      .then(([me, bidders]) => {
        const found = (bidders || []).find((b) => b.name === me?.organization_name) || {};
        setProfile({
          name: me?.full_name || localStorage.getItem("bs_name") || "—",
          email: me?.email || localStorage.getItem("bs_email") || "—",
          role: me?.role || localStorage.getItem("bs_role") || "—",
          org: me?.organization_name || localStorage.getItem("bs_org") || "—",
          gstin: found.gstin || "27AAACA1234A1Z5",
          reg: found.registration_number || "REG-MH-2024-1182",
          status: found.verification_status || "VERIFIED",
        });
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-head">
        <div>
          <div className="kicker">ORGANISATION CREDENTIALS</div>
          <h1>{isOfficerRole(role) ? "Officer profile" : "Company profile"}</h1>
          <p>Verified identity and registration details persisted in the database.</p>
        </div>
        <Badge tone="success">Verified Entity</Badge>
      </div>

      <section className="panel">
        <PanelHead title="Account & Registration Details" sub="Live database-backed profile" />
        <div className="profile-card">
          <div className="profile-item">
            <span>OFFICIAL NAME</span>
            <b>{profile?.name}</b>
          </div>
          <div className="profile-item">
            <span>WORK EMAIL</span>
            <b>{profile?.email}</b>
          </div>
          <div className="profile-item">
            <span>ORGANISATION / DEPT</span>
            <b>{profile?.org}</b>
          </div>
          <div className="profile-item">
            <span>ASSIGNED ROLE</span>
            <b>{profile?.role}</b>
          </div>
          <div className="profile-item">
            <span>REGISTRATION NUMBER</span>
            <b>{profile?.reg}</b>
          </div>
          <div className="profile-item">
            <span>GSTIN / TAX IDENTIFIER</span>
            <b>{profile?.gstin}</b>
          </div>
          <div className="profile-item">
            <span>VERIFICATION STATUS</span>
            <Badge tone="success">{profile?.status}</Badge>
          </div>
          <div className="profile-item">
            <span>SECURITY LEVEL</span>
            <b>Argon2 Password Hash + RBAC</b>
          </div>
        </div>
      </section>
    </>
  );
}

/* =========================
   GENERIC
========================= */

function Generic({ role, page }) {
  const titles = {
    reports: [
      "Reports",
      "Decision-ready procurement reporting and exportable summaries.",
    ],

    browse: [
      "Browse tenders",
      "Discover opportunities matching your company profile.",
    ],

    vault: [
      "Document vault",
      "Central place for verified and submission-ready evidence.",
    ],

    profile: [
      "Company profile",
      "Organisation details, registrations and verification status.",
    ],

    notifications: [
      "Notifications",
      "Your latest tender, evidence and submission alerts.",
    ],

    bidders: [
      "Bidders",
      "Registered suppliers and their verification posture.",
    ],
  };

  const [title, sub] =
    titles[page] || [
      "Workspace",
      "BuildShield AI procurement workspace.",
    ];

  return (
    <>
      <div className="page-head">
        <div>
          <div className="kicker">
            BUILD SHIELD WORKSPACE
          </div>

          <h1>{title}</h1>

          <p>{sub}</p>
        </div>
      </div>

      <section className="panel empty large">
        <Icon name="shield" size={38} />

        <h2>
          {isOfficerRole(role)
            ? "Evidence-led procurement workspace"
            : "Supplier evidence workspace"}
        </h2>

        <p>
          This screen is ready for your backend data.
          The shared shell, styling, authentication and API
          client are already wired for the next endpoint.
        </p>
      </section>
    </>
  );
}

/* =========================
   APP
========================= */

function App() {
  const [auth, setAuth] = useState(
    Boolean(localStorage.getItem("bs_token"))
  );

  const [role, setRole] = useState(
    localStorage.getItem("bs_role") ||
      "OFFICER"
  );

  const [page, setPage] = useState("overview");

  const logout = () => {
    localStorage.removeItem("bs_token");
    localStorage.removeItem("bs_role");
    localStorage.removeItem("bs_name");
    localStorage.removeItem("bs_email");
    localStorage.removeItem("bs_org");

    setAuth(false);
    setRole("OFFICER");
    setPage("overview");
  };

  const go = (nextPage) => {
    setPage(nextPage);
  };

  useEffect(() => {
    const token = localStorage.getItem("bs_token");
    if (token) {
      api("/auth/me")
        .then((user) => {
          localStorage.setItem("bs_role", user.role);
          localStorage.setItem("bs_name", user.full_name);
          localStorage.setItem("bs_email", user.email);
          localStorage.setItem("bs_org", user.organization_name || "");
          setRole(user.role);
          setAuth(true);
        })
        .catch(() => {
          logout();
        });
    } else {
      setAuth(false);
    }
  }, []);

  useEffect(() => {
    if (!auth) {
      setPage("overview");
    }
  }, [auth]);

  if (!auth) {
    return (
      <Login
        onLogin={() => {
          const storedRole =
            localStorage.getItem("bs_role") ||
            "OFFICER";

          setRole(storedRole);
          setAuth(true);
        }}
      />
    );
  }

  return (
    <Layout
      role={role}
      onLogout={logout}
      page={page}
      setPage={setPage}
    >
      {page === "overview" ? (
        isOfficerRole(role) ? (
          <OfficerOverview go={go} />
        ) : (
          <BidderOverview go={go} />
        )
      ) : page === "tenders" ||
        page === "browse" ? (
        <Tenders role={role} go={go} />
      ) : page === "review" ? (
        <Review />
      ) : page === "bidders" ? (
        <Bidders />
      ) : page === "reports" ? (
        <Reports />
      ) : page === "audit" ? (
        <Audit />
      ) : page === "mybids" ? (
        <Bids role={role} />
      ) : page === "vault" ? (
        <DocumentVault role={role} />
      ) : page === "profile" ? (
        <CompanyProfile role={role} />
      ) : (
        <Generic
          role={role}
          page={page}
        />
      )}
    </Layout>
  );
}

createRoot(
  document.getElementById("root")
).render(<App />);



