import React, { useState } from "react";
import { apiFetch } from "../api.js";

export default function ChatPanel({ onAction }) {
  const [msg, setMsg] = useState("mostrame pendientes");
  const [log, setLog] = useState([]);

  async function send() {
    const userMsg = msg;
    setLog(l => [...l, { from:"user", text: userMsg }]);
    setMsg("");
    try {
      const res = await apiFetch("/v1/chat", {
        method:"POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({ message: userMsg })
      });
      setLog(l => [...l, { from:"bot", text: res.reply, data: res.data }]);
      onAction?.();
    } catch (e) {
      setLog(l => [...l, { from:"bot", text: `Error: ${String(e.message)}` }]);
    }
  }

  return (
    <div>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div style={{ fontWeight: 800 }}>Chat (POC)</div>
        <span className="badge">Tools</span>
      </div>

      <div className="chatLog" style={{ marginTop: 10 }}>
        {log.length === 0 && (
          <div style={{ color:"var(--muted)", fontSize: 13 }}>
            Sugerencias: <br/>
            • "mostrame pendientes" <br/>
            • "venta 13300 libreria" <br/>
            • "ultimas transacciones"
          </div>
        )}
        {log.map((m, i) => (
          <div key={i} className="msg">
            <b style={{ color: m.from === "bot" ? "var(--brand)" : "var(--text)" }}>{m.from}:</b> {m.text}
            {m.data && <pre style={{ whiteSpace:"pre-wrap", marginTop: 8 }}>{JSON.stringify(m.data, null, 2)}</pre>}
          </div>
        ))}
      </div>

      <div style={{ display:"flex", gap:10, marginTop: 10 }}>
        <input value={msg} onChange={e=>setMsg(e.target.value)} placeholder='Escribí: "venta 13300 libreria"' />
        <button className="primary" onClick={send} disabled={!msg.trim()}>Enviar</button>
      </div>
    </div>
  );
}
