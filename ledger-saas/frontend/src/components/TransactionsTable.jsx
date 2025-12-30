import React from "react";

function Pill({ text, tone }) {
  const bg = tone === "good" ? "rgba(42,168,184,0.12)" : tone === "warn" ? "rgba(245,158,11,0.14)" : "rgba(107,114,128,0.10)";
  const br = tone === "good" ? "rgba(42,168,184,0.25)" : tone === "warn" ? "rgba(245,158,11,0.30)" : "rgba(107,114,128,0.18)";
  const cl = tone === "good" ? "#0b6aa7" : tone === "warn" ? "#a16207" : "#374151";
  return (
    <span style={{ padding:"6px 10px", borderRadius:999, border:`1px solid ${br}`, background:bg, color:cl, fontSize:12 }}>
      {text}
    </span>
  );
}

export default function TransactionsTable({ rows }) {
  return (
    <div>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom: 10 }}>
        <div style={{ fontWeight: 800 }}>Transacciones</div>
        <span className="badge">Mostrando {rows.length}</span>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Paciente / Contraparte</th>
            <th>Último movimiento</th>
            <th>Monto</th>
            <th>Match</th>
            <th>Review</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => {
            const matchTone = r.match_status === "matched" ? "good" : r.match_status === "ambiguous" ? "warn" : "neutral";
            return (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td style={{ maxWidth: 240 }}>
                  <div style={{ fontWeight: 700 }}>{r.payer_name || r.payee_name || "-"}</div>
                  <div style={{ color:"var(--muted)", fontSize: 12 }}>{r.source_file}</div>
                </td>
                <td>
                  <div style={{ color:"var(--muted)", fontSize: 12 }}>{r.source_system} / {r.doc_type}</div>
                  <div style={{ fontSize: 12 }}>{r.operation_id || "-"}</div>
                </td>
                <td style={{ fontWeight: 800 }}>
                  {(r.amount ?? "-")} {r.currency}
                </td>
                <td>
                  <Pill text={`${r.match_status}${r.match_score ? " " + r.match_score : ""}`} tone={matchTone} />
                </td>
                <td>
                  {r.needs_review ? <Pill text="Sí" tone="warn" /> : <Pill text="No" tone="good" />}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
