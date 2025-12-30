import React, { useState } from "react";
import { apiFetch } from "../api.js";

export default function CreateUser({ onDone }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("employee");
  const [whatsappNumber, setWhatsappNumber] = useState("");
  const [whatsappWaId, setWhatsappWaId] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      const payload = {
        email,
        password,
        role,
        whatsapp_number: whatsappNumber || null,
        whatsapp_wa_id: whatsappWaId || null,
      };

      const result = await apiFetch("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setEmail("");
      setPassword("");
      setRole("employee");
      setWhatsappNumber("");
      setWhatsappWaId("");
      setErr(null);
      onDone();
    } catch (e) {
      setErr(String(e.message));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        <div>
          <label style={{ display: "block", fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="usuario@example.com"
            required
          />
        </div>

        <div>
          <label style={{ display: "block", fontSize: 12, color: "var(--muted)", marginBottom: 4 }}>Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Min. 8 caracteres"
            required
          />
        </div>

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

        <button type="submit" disabled={loading}>
          {loading ? "Creando..." : "Crear usuario"}
        </button>
      </div>
    </form>
  );
}
