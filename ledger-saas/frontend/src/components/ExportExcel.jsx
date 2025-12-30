import React, { useState } from "react";
import { API_BASE, getToken } from "../api.js";

export default function ExportExcel() {
  const [busy, setBusy] = useState(false);

  async function download() {
    setBusy(true);
    try {
      const res = await fetch(`${API_BASE}/v1/export/transactions.xlsx`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (!res.ok) throw new Error(await res.text());
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "transactions.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button onClick={download} className="primary" disabled={busy}>
      {busy ? "Exportando..." : "Export Excel"}
    </button>
  );
}
