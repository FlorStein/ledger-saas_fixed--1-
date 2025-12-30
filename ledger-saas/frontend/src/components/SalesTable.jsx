import React from "react";

export default function SalesTable({ rows }) {
  return (
    <div className="tableWrap">
      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Fecha/hora</th>
            <th>Monto</th>
            <th>Comprador</th>
            <th>CUIT</th>
            <th>Teléfono</th>
            <th>Ref</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={8} style={{ color: "var(--muted)", padding: 18 }}>
                No hay ventas cargadas.
              </td>
            </tr>
          )}
          {rows.map(r => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.datetime}</td>
              <td style={{ fontWeight: 700 }}>{Number(r.amount).toLocaleString("es-AR")} {r.currency}</td>
              <td>{r.customer_name || "—"}</td>
              <td>{r.customer_cuit || "—"}</td>
              <td>{r.customer_phone || "—"}</td>
              <td>{r.external_ref || "—"}</td>
              <td><span className="badge">{r.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
