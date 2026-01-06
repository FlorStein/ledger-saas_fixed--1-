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

function Sidebar({ active, setActive, setTab, onLogout }) {
  const items = [
    { key:"ledger", label:"Comprobantes", icon:"📑", tab:"Comprobantes" },
    { key:"sales", label:"Ventas", icon:"💰", tab:"Ventas" },
    { key:"clients", label:"Clientes", icon:"👥", tab:"Clientes" },
    { key:"campaigns", label:"Campañas", icon:"📣", tab:"Campañas" },
    { key:"stats", label:"Estadísticas", icon:"📊", tab:"Estadísticas" },
    { key:"settings", label:"Configuración", icon:"⚙️", tab:"Configuración" },
  ];
  return (
    <div className="sidebarWrap card" style={{ padding: 10, border: "none" }}>
      <div className="sidebar">
        <div className="navbtn active" title="Home" style={{ marginBottom: 6 }}>🏠</div>
        {items.map(it => (
          <div key={it.key}
               className={"navbtn " + (active===it.key ? "active": "")}
               title={it.label}
               onClick={()=>{ setActive(it.key); setTab(it.tab); }}>
            {it.icon}
          </div>
        ))}
        <div style={{ flex: 1 }} />
        <div className="navbtn" title="Logout" onClick={onLogout}>🚪</div>
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
  const [showPassword, setShowPassword] = useState(false);

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

  const currentUser = useMemo(() => {
    if (users && users.length) {
      return users.find(u => u.role === "owner") || users[0];
    }
    return null;
  }, [users]);

  const accountInfo = {
    username: currentUser?.email?.split("@")?.[0] || "—",
    email: currentUser?.email || "—",
    password: currentUser?.password_placeholder || "demo123",
  };

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

  const customers = useMemo(() => {
    const byKey = new Map();
    sales.forEach((s) => {
      const key = (s.customer_name || "Sin nombre") + (s.customer_phone || "");
      const current = byKey.get(key) || {
        name: s.customer_name || "Sin nombre",
        phone: s.customer_phone || "-",
        lastSale: s.datetime || s.created_at || "",
        totalAmount: 0,
        count: 0,
      };
      current.totalAmount += Number(s.amount || 0);
      current.count += 1;
      current.lastSale = s.datetime || current.lastSale;
      byKey.set(key, current);
    });
    return Array.from(byKey.values());
  }, [sales]);

  const filteredCustomers = useMemo(() => {
    const s = search.trim().toLowerCase();
    if (!s) return customers;
    return customers.filter((c) =>
      (c.name || "").toLowerCase().includes(s) ||
      (c.phone || "").toLowerCase().includes(s)
    );
  }, [customers, search]);

  const resultsCount = useMemo(() => {
    if (tab === "Ventas") return filteredSales.length;
    if (tab === "Users") return users.length;
    if (tab === "Clientes") return filteredCustomers.length;
    return filteredTx.length;
  }, [tab, filteredSales, filteredCustomers, filteredTx, users]);

  return (
    <div className="layout">
      <Sidebar active={active} setActive={setActive} setTab={setTab} onLogout={onLogout} />

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
            {["Comprobantes","Ventas","Users","Campañas","Clientes","Estadísticas","Configuración"].map(t => (
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
            <div className="badge dot">Resultados: {resultsCount}</div>
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

        {tab === "Clientes" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Clientes</div>
              <div style={{ color:"var(--muted)", fontSize: 13, marginBottom: 12 }}>
                Resumen generado a partir de las ventas cargadas (nombre, teléfono, volumen y última compra).
              </div>
              <div style={{ maxHeight: 420, overflowY: "auto" }}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>Nombre</th>
                      <th>Teléfono</th>
                      <th>Órdenes</th>
                      <th>Última compra</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCustomers.map((c, idx) => (
                      <tr key={idx}>
                        <td>{c.name}</td>
                        <td>{c.phone}</td>
                        <td>{c.count}</td>
                        <td>${c.totalAmount.toLocaleString("es-AR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                        <td>{c.lastSale ? new Date(c.lastSale).toLocaleDateString("es-AR") : "-"}</td>
                      </tr>
                    ))}
                    {filteredCustomers.length === 0 && (
                      <tr><td colSpan="5" style={{ textAlign:"center", color:"var(--muted)" }}>Sin clientes aún</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Acciones rápidas</div>
              <ul style={{ margin: 0, paddingLeft: 16, color:"var(--muted)", lineHeight: 1.6 }}>
                <li>Exportar cartera para campañas</li>
                <li>Enviar recordatorios de pago a deudores</li>
                <li>Crear segmento por volumen o frecuencia</li>
                <li>Registrar una nota sobre el cliente</li>
              </ul>
            </div>
          </div>
        )}

        {tab === "Estadísticas" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Resumen rápido</div>
              <div style={{ display:"grid", gap:10 }}>
                <div className="kpi">
                  <div className="label">Oportunidad total</div>
                  <div className="value">{kpis.total.toLocaleString("es-AR",{minimumFractionDigits:2, maximumFractionDigits:2})} ARS</div>
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
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Próximas mejoras</div>
              <ul style={{ margin:0, paddingLeft:16, color:"var(--muted)", lineHeight:1.6 }}>
                <li>Embudo por origen de ingreso</li>
                <li>Tiempo medio de conciliación</li>
                <li>Alertas de riesgo en clientes</li>
              </ul>
            </div>
          </div>
        )}

        {tab === "Configuración" && (
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Preferencias básicas</div>
              <div style={{ display:"grid", gap:12 }}>
                <div style={{ display:"grid", gap:8 }}>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>Alertas</div>
                  <label style={{ display:"grid", gridTemplateColumns:"1fr auto", alignItems:"center", columnGap:12 }}>
                    <span>Notificaciones por email</span>
                    <input type="checkbox" defaultChecked style={{ width:18, height:18, minWidth:18 }} />
                  </label>
                  <label style={{ display:"grid", gridTemplateColumns:"1fr auto", alignItems:"center", columnGap:12 }}>
                    <span>Avisar transacciones sin match</span>
                    <input type="checkbox" style={{ width:18, height:18, minWidth:18 }} />
                  </label>
                </div>
                <div style={{ display:"grid", gap:6 }}>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>Moneda por defecto</div>
                  <select defaultValue="ARS">
                    <option value="ARS">ARS</option>
                    <option value="USD">USD</option>
                  </select>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>Usada para KPIs y totales.</div>
                </div>
                <div style={{ display:"flex", justifyContent:"flex-end" }}>
                  <button className="secondary">Guardar preferencias</button>
                </div>
              </div>
            </div>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Integraciones</div>
              <ul style={{ margin:0, paddingLeft:16, color:"var(--muted)", lineHeight:1.6 }}>
                <li>WhatsApp Cloud API</li>
                <li>Exportar a Excel</li>
                <li>Webhook de ingestión</li>
              </ul>
            </div>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Información de cuenta</div>
              <div style={{ color:"var(--muted)", fontSize: 13, marginBottom: 10 }}>
                Datos actuales del usuario. Puedes ver la contraseña temporalmente con el icono de ojo.
              </div>
              <div style={{ display:"grid", gap:10 }}>
                <div>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>Usuario</div>
                  <div style={{ fontWeight:700 }}>{accountInfo.username}</div>
                </div>
                <div>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>Email</div>
                  <div style={{ fontWeight:700 }}>{accountInfo.email}</div>
                </div>
                <div>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>Contraseña</div>
                  <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                    <span style={{ fontFamily:"monospace" }}>
                      {showPassword ? accountInfo.password : "••••••••"}
                    </span>
                    <button className="secondary" onClick={()=>setShowPassword(v=>!v)}>{showPassword ? "👁‍🗨 Ocultar" : "👁 Ver"}</button>
                  </div>
                  {showPassword && (
                    <div style={{ color:"var(--muted)", fontSize: 12, marginTop: 4 }}>
                      Demo: mostramos la clave que usaste al ingresar (en producción se almacena hasheada).
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="card" style={{ padding: 12 }}>
              <div style={{ fontWeight: 800, marginBottom: 8 }}>Seguridad de cuenta</div>
              <div style={{ color:"var(--muted)", fontSize: 13, marginBottom: 10 }}>
                Cambia tu usuario y clave. Enviamos un código al email (y opcionalmente a WhatsApp) para validar la identidad antes de aplicar cambios.
              </div>
              <div style={{ display:"grid", gap:10 }}>
                <label style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  <span>Nuevo usuario</span>
                  <input type="text" placeholder="tu.nuevo.usuario" />
                </label>
                <label style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  <span>Nuevo email</span>
                  <input type="email" placeholder="tu@mail.com" />
                </label>
                <label style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  <span>Nueva contraseña</span>
                  <input type="password" placeholder="********" />
                </label>
                <label style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  <span>Código enviado al email</span>
                  <input type="text" placeholder="123456" />
                </label>
                <label style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  <span>WhatsApp para 2FA</span>
                  <input type="tel" placeholder="Ej: +54911..." />
                </label>
                <label style={{ display:"flex", flexDirection:"column", gap:6 }}>
                  <span>Código enviado por WhatsApp</span>
                  <input type="text" placeholder="654321" />
                </label>
                <div style={{ display:"flex", gap:8 }}>
                  <button>Enviar código email</button>
                  <button>Enviar código WhatsApp</button>
                  <button className="secondary">Guardar cambios</button>
                </div>
                <div style={{ color:"var(--muted)", fontSize: 12 }}>
                  Se requiere validación por correo y/o WhatsApp para evitar cambios no autorizados.
                </div>
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
