import React, { useState } from "react";
import { apiFetch } from "../api.js";

export default function EditUser({ user, onDone, onCancel }) {
  const [role, setRole] = useState(user.role);
  const [whatsappNumber, setWhatsappNumber] = useState(user.whatsapp_number || "");
  const [whatsappWaId, setWhatsappWaId] = useState(user.whatsapp_wa_id || "");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      const payload = {
        role: role !== user.role ? role : undefined,
        whatsapp_number: whatsappNumber !== user.whatsapp_number ? whatsappNumber || null : undefined,
        whatsapp_wa_id: whatsappWaId !== user.whatsapp_wa_id ? whatsappWaId || null : undefined,
      };

      await apiFetch(`/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      onDone();
    } catch (e) {
      setErr(String(e.message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div style={{ fontSize: 13, fontWeight: 700 }}>Editar: {user.email}</div>

      <div>
        <label style={{ display: "block", fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Rol</label>
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="owner">Owner</option>
          <option value="admin">Admin</option>
          <option value="employee">Employee</option>
          <option value="viewer">Viewer</option>
        </select>
      </div>

      <div>
        <label style={{ display: "block", fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>WhatsApp Number (E.164)</label>
        <input
          type="text"
          value={whatsappNumber}
          onChange={(e) => setWhatsappNumber(e.target.value)}
          placeholder="+54911234567890"
        />
      </div>

      <div>
        <label style={{ display: "block", fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>WhatsApp WA ID (dígitos)</label>
        <input
          type="text"
          value={whatsappWaId}
          onChange={(e) => setWhatsappWaId(e.target.value)}
          placeholder="54911234567890"
        />
      </div>

      {err && <div style={{ color: "var(--error)", fontSize: 12 }}>{err}</div>}

      <div style={{ display: "flex", gap: 10 }}>
        <button type="submit" disabled={loading} style={{ flex: 1 }}>
          {loading ? "Guardando..." : "Guardar"}
        </button>
        <button type="button" onClick={onCancel} style={{ flex: 1, background: "var(--muted)" }}>
          Cancelar
        </button>
      </div>
    </form>
  );
}
