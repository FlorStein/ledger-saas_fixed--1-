import React, { useState } from "react";
import EditUser from "./EditUser.jsx";

export default function UsersTable({ rows }) {
  const [editingId, setEditingId] = useState(null);

  const editingUser = rows.find((u) => u.id === editingId);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {editingUser && (
        <div style={{ padding: 12, background: "var(--bg-secondary)", borderRadius: 4 }}>
          <EditUser
            user={editingUser}
            onDone={() => {
              setEditingId(null);
              // onRefresh would be passed as prop if needed
            }}
            onCancel={() => setEditingId(null)}
          />
        </div>
      )}

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ borderBottom: "2px solid var(--border)" }}>
              <th style={{ padding: 8, textAlign: "left", fontWeight: 700 }}>Email</th>
              <th style={{ padding: 8, textAlign: "left", fontWeight: 700 }}>Rol</th>
              <th style={{ padding: 8, textAlign: "left", fontWeight: 700 }}>WhatsApp Number</th>
              <th style={{ padding: 8, textAlign: "left", fontWeight: 700 }}>WA ID</th>
              <th style={{ padding: 8, textAlign: "center", fontWeight: 700 }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((user) => (
              <tr
                key={user.id}
                style={{
                  borderBottom: "1px solid var(--border)",
                  background: editingId === user.id ? "var(--bg-secondary)" : "transparent",
                }}
              >
                <td style={{ padding: 8 }}>
                  <div style={{ fontWeight: 500 }}>{user.email}</div>
                </td>
                <td style={{ padding: 8 }}>
                  <span
                    style={{
                      padding: "2px 8px",
                      background: user.role === "owner" ? "#e8f5e9" : "#f0f4ff",
                      color: user.role === "owner" ? "#2e7d32" : "#1565c0",
                      borderRadius: 3,
                      fontSize: 12,
                      fontWeight: 600,
                    }}
                  >
                    {user.role}
                  </span>
                </td>
                <td style={{ padding: 8 }}>
                  <code style={{ fontSize: 12, background: "var(--bg-secondary)", padding: "2px 6px", borderRadius: 3 }}>
                    {user.whatsapp_number || "-"}
                  </code>
                </td>
                <td style={{ padding: 8 }}>
                  <code style={{ fontSize: 12, background: "var(--bg-secondary)", padding: "2px 6px", borderRadius: 3 }}>
                    {user.whatsapp_wa_id || "-"}
                  </code>
                </td>
                <td style={{ padding: 8, textAlign: "center" }}>
                  <button
                    onClick={() => setEditingId(user.id)}
                    style={{
                      padding: "4px 10px",
                      fontSize: 12,
                      background: "var(--primary)",
                      color: "white",
                      border: "none",
                      borderRadius: 3,
                      cursor: "pointer",
                    }}
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {rows.length === 0 && (
        <div style={{ textAlign: "center", padding: 20, color: "var(--muted)" }}>
          No hay usuarios para mostrar
        </div>
      )}
    </div>
  );
}
