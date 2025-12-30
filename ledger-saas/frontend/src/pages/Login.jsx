import React, { useState } from "react";
import { apiFetch, setToken } from "../api.js";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("owner@demo.com");
  const [password, setPassword] = useState("demo123");
  const [err, setErr] = useState(null);

  async function submit(e) {
    e.preventDefault();
    setErr(null);
    try {
      const data = await apiFetch("/auth/login", {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ email, password })
      });
      setToken(data.access_token);
      onLogin();
    } catch (e2) {
      setErr(String(e2.message));
    }
  }

  return (
    <div style={{ display:"grid", placeItems:"center", height:"100vh", padding:16 }}>
      <div className="card" style={{ width: 430, padding: 18 }}>
        <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18 }}>Ledger SaaS</div>
            <div style={{ color:"var(--muted)", fontSize: 13, marginTop: 4 }}>POC multi-tenant (demo)</div>
          </div>
          <span className="badge dot">Secure</span>
        </div>

        <form onSubmit={submit} style={{ display:"grid", gap:10, marginTop: 14 }}>
          <label style={{ fontSize: 13, color:"var(--muted)" }}>Email</label>
          <input value={email} onChange={e=>setEmail(e.target.value)} />
          <label style={{ fontSize: 13, color:"var(--muted)" }}>Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <button className="primary" style={{ marginTop: 8 }}>Login</button>
          {err && <pre style={{ whiteSpace:"pre-wrap" }}>{err}</pre>}
          <div style={{ color:"var(--muted)", fontSize: 12, marginTop: 6 }}>
            Demo: owner@demo.com / demo123
          </div>
        </form>
      </div>
    </div>
  );
}
