import React, { useEffect, useMemo, useState } from "react";
import UploadReceipt from "../components/UploadReceipt.jsx";
import ExportExcel from "../components/ExportExcel.jsx";
import CreateSale from "../components/CreateSale.jsx";
import UploadSaleImage from "../components/UploadSaleImage.jsx";
import TransactionsTable from "../components/TransactionsTable.jsx";
import SalesTable from "../components/SalesTable.jsx";
import ChatPanel from "../components/ChatPanel.jsx";
import CreateUser from "../components/CreateUser.jsx";
import UsersTable from "../components/UsersTable.jsx";
import { apiFetch } from "../api.js";

function Sidebar({ active, setActive }) {
  const items = [
    { key:"ledger", label:"Ledger" },
    { key:"sales", label:"Ventas" },
    { key:"users", label:"Users" },
    { key:"tasks", label:"Tareas" },
    { key:"settings", label:"Settings" },
  ];
  return (
    <div className="sidebarWrap card" style={{ padding: 10, border: "none" }}>
      <div className="sidebar">
        <div className="navbtn active" title="Home" style={{ marginBottom: 6 }}>L</div>
        {items.map(it => (
          <div key={it.key}
               className={"navbtn " + (active===it.key ? "active": "")}
               title={it.label}
               onClick={()=>setActive(it.key)}>
            {it.label[0]}
          </div>
        ))}
        <div style={{ flex: 1 }} />
        <div className="navbtn" title="Logout">⚙</div>
      </div>
    </div>
  );
}

export default function Dashboard({ onLogout }) {
  const [tx, setTx] = useState([]);
  const [sales, setSales] = useState([]);
  const [users, setUsers] = useState([]);
  const [tab, setTab] = useState("Comprobantes");
  const [active, setActive] = useState("ledger");
  const [search, setSearch] = useState("");
  const [err, setErr] = useState(null);

  async function refreshAll() {
    setErr(null);
    try {
      const [tData, sData, uData] = await Promise.all([
        apiFetch("/v1/transactions"),
        apiFetch("/v1/sales"),
        apiFetch("/users"),
      ]);
      setTx(tData);
      setSales(sData);
      setUsers(uData || []);
    } catch (e) {
      setErr(String(e.message));
    }
  }
  useEffect(() => { refreshAll(); }, []);

  const kpis = useMemo(() => {
    const total = tx.reduce((a,r)=>a+(r.amount||0),0);
    const review = tx.filter(r=>r.needs_review).length;
    const matched = tx.filter(r=>r.match_status==="matched").length;
    return { total, review, matched };
  }, [tx]);

  const filteredTx = useMemo(() => {
    const s = search.trim().toLowerCase();
    if (!s) return tx;
    return tx.filter(r =>
      String(r.id).includes(s) ||
      (r.source_file||"").toLowerCase().includes(s) ||
      (r.payer_name||"").toLowerCase().includes(s) ||
      (r.payee_name||"").toLowerCase().includes(s)
    );
  }, [tx, search]);

  const filteredSales = useMemo(() => {
    const s = search.trim().toLowerCase();
    if (!s) return sales;
    return sales.filter(r =>
      String(r.id).includes(s) ||
      (r.description||"").toLowerCase().includes(s) ||
      (r.customer_name||"").toLowerCase().includes(s) ||
      (r.customer_cuit||"").toLowerCase().includes(s) ||
      (r.customer_phone||"").toLowerCase().includes(s) ||
      (r.external_ref||"").toLowerCase().includes(s)
    );
  }, [sales, search]);

  return (
    <div className="layout">
      <Sidebar active={active} setActive={setActive} />

      <div className="main">
        <div className="card topbar">
          <div className="search">
            <span style={{ color:"var(--muted)" }}>🔎</span>
            <input placeholder="Buscar (archivo, persona, id)..." value={search} onChange={e=>setSearch(e.target.value)} />
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <span className="badge">Demo tenant</span>
            <ExportExcel />
            <button onClick={onLogout}>Salir</button>
          </div>
        </div>

        <div className="card">
          <div className="tabs">
            {["Comprobantes","Ventas","Users","Campañas","Cumpleaños"].map(t => (
              <div key={t} className={"tab " + (tab===t ? "active": "")} onClick={()=>setTab(t)}>{t}</div>
            ))}
          </div>

          <div className="filters">
            <div className="f">
              <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Estado</div>
              <select>
                <option>Todos</option>
                <option>Matcheados</option>
                <option>Pendientes</option>
              </select>
            </div>
            <div className="f">
              <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Período</div>
              <select>
                <option>Mes actual</option>
                <option>Mes pasado</option>
                <option>Últimos 90 días</option>
              </select>
            </div>
            <div style={{ flex: 1 }} />
            <div className="badge dot">Resultados: {tab === "Ventas" ? filteredSales.length : filteredTx.length}</div>
          </div>
        </div>

        {tab === "Comprobantes" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div className="card" style={{ padding: 12 }}>
              <UploadReceipt onDone={refreshAll} />
            </div>
            <div className="card" style={{ padding: 12 }}>
              <CreateSale onDone={refreshAll} />
            </div>
          </div>
        )}

        {tab === "Users" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 12 }}>Crear usuario</div>
              <CreateUser onDone={refreshAll} />
            </div>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 800 }}>Usuarios</div>
                  <div style={{ color:"var(--muted)", fontSize: 13, marginTop: 4 }}>
                    Equipo del tenant actual
                  </div>
                </div>
                <button onClick={refreshAll}>Refrescar</button>
              </div>
              <UsersTable rows={users} />
            </div>
          </div>
        )}

        {tab === "Ventas" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ display:"grid", gap:12 }}>
                <div>
                  <CreateSale onDone={refreshAll} />
                </div>
                <hr style={{ margin:0, opacity: 0.2 }} />
                <div>
                  <UploadSaleImage onDone={refreshAll} />
                </div>
              </div>
            </div>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                <div>
                  <div style={{ fontWeight: 800 }}>Ventas</div>
                  <div style={{ color:"var(--muted)", fontSize: 13, marginTop: 4 }}>
                    Cargadas en la base del tenant actual
                  </div>
                </div>
                <button onClick={refreshAll}>Refrescar</button>
              </div>
              <div style={{ marginTop: 12 }}>
                <SalesTable rows={filteredSales} />
              </div>
            </div>
          </div>
        )}

        {err && <pre style={{ whiteSpace:"pre-wrap" }}>{err}</pre>}

        {tab === "Comprobantes" && (
          <div className="card" style={{ padding: 12 }}>
            <TransactionsTable rows={filteredTx} />
          </div>
        )}
      </div>

      <div className="panelRight">
        <div className="card" style={{ padding: 12 }}>
          <div style={{ display:"grid", gap:10 }}>
            <div className="kpi">
              <div className="label">Oportunidad total (ARS)</div>
              <div className="value">{kpis.total.toLocaleString("es-AR",{minimumFractionDigits:2, maximumFractionDigits:2})}</div>
            </div>
            <div className="kpi">
              <div className="label">Pendientes de revisión</div>
              <div className="value">{kpis.review}</div>
            </div>
            <div className="kpi">
              <div className="label">Matcheadas</div>
              <div className="value">{kpis.matched}</div>
            </div>
          </div>
        </div>

        <div className="card" style={{ padding: 12 }}>
          <ChatPanel onAction={refreshAll} />
        </div>
      </div>
    </div>
  );
}
