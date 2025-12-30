import React, { useState } from "react";
import { API_BASE, getToken } from "../api.js";

export default function UploadReceipt({ onDone }) {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState(null);

  async function submit() {
    setMsg(null);
    if (!file) return;

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/v1/receipts`, {
        method: "POST",
        headers: { Authorization: `Bearer ${getToken()}` },
        body: form
      });

      const txt = await res.text();
      if (!res.ok) {
        throw new Error(txt || `HTTP ${res.status}`);
      }
      const data = txt ? JSON.parse(txt) : {};
      setMsg(JSON.stringify(data, null, 2));
      onDone?.();
    } catch (e) {
      setMsg(`Error: ${String(e.message)}`);
    }
  }

  return (
    <div>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <div>
          <div style={{ fontWeight: 800 }}>Subir comprobante (PDF)</div>
          <div style={{ color:"var(--muted)", fontSize: 13, marginTop: 4 }}>
            Pipeline: extracción → contrapartes → match con ventas
          </div>
        </div>
        <span className="badge dot">Upload</span>
      </div>

      <div style={{ display:"flex", gap:10, alignItems:"center", marginTop: 12 }}>
        <input type="file" accept="application/pdf" onChange={(e)=>setFile(e.target.files?.[0])} />
        <button className="primary" onClick={submit} disabled={!file}>Procesar</button>
      </div>

      {msg && <pre style={{ whiteSpace:"pre-wrap", marginTop: 12 }}>{msg}</pre>}
    </div>
  );
}
