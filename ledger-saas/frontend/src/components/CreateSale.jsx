import React, { useState } from "react";
import { apiFetch } from "../api.js";

export default function CreateSale({ onDone }) {
  const [amount, setAmount] = useState("13300");
  const [desc, setDesc] = useState("Art. librería");
  const [datetime, setDatetime] = useState("2025-12-29T10:35:00");
  const [customerName, setCustomerName] = useState("");
  const [customerCuit, setCustomerCuit] = useState("");
  const [customerPhone, setCustomerPhone] = useState("");
  const [externalRef, setExternalRef] = useState("");
  const [msg, setMsg] = useState(null);

  async function submit() {
    setMsg(null);
    try {
      const payload = {
        datetime,
        amount: Number(amount),
        currency: "ARS",
        description: desc,
        customer_name: customerName.trim() || null,
        customer_cuit: customerCuit.trim() || null,
        customer_phone: customerPhone.trim() || null,
        external_ref: externalRef.trim() || null,
      };

      const data = await apiFetch("/v1/sales", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      setMsg(`Venta creada: #${data.id}`);
      onDone?.();
    } catch (e) {
      setMsg(`Error: ${String(e.message)}`);
    }
  }

  return (
    <div>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <div style={{ fontWeight: 800 }}>Crear venta (demo)</div>
          <div style={{ color:"var(--muted)", fontSize: 13, marginTop: 4 }}>
            Usala para probar conciliación automática por monto + fecha
          </div>
        </div>
        <span className="badge">Sales</span>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginTop: 12 }}>
        <div>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Monto</div>
          <input value={amount} onChange={e=>setAmount(e.target.value)} />
        </div>
        <div>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Fecha/hora (ISO)</div>
          <input value={datetime} onChange={e=>setDatetime(e.target.value)} />
        </div>
        <div style={{ gridColumn:"1 / -1" }}>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Descripción</div>
          <input value={desc} onChange={e=>setDesc(e.target.value)} />
        </div>

        <div style={{ gridColumn:"1 / -1" }}>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Comprador (nombre)</div>
          <input placeholder="Opcional" value={customerName} onChange={e=>setCustomerName(e.target.value)} />
        </div>
        <div>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>CUIT</div>
          <input placeholder="Opcional" value={customerCuit} onChange={e=>setCustomerCuit(e.target.value)} />
        </div>
        <div>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Teléfono</div>
          <input placeholder="Opcional" value={customerPhone} onChange={e=>setCustomerPhone(e.target.value)} />
        </div>
        <div style={{ gridColumn:"1 / -1" }}>
          <div style={{ fontSize: 12, color:"var(--muted)", marginBottom: 6 }}>Referencia (external_ref)</div>
          <input placeholder="Opcional" value={externalRef} onChange={e=>setExternalRef(e.target.value)} />
        </div>
      </div>

      <div style={{ display:"flex", alignItems:"center", gap:10, marginTop: 12 }}>
        <button className="primary" onClick={submit}>Crear</button>
        {msg && <span className="badge" style={{ maxWidth: 330, overflow:"hidden", textOverflow:"ellipsis" }}>{msg}</span>}
      </div>
    </div>
  );
}
