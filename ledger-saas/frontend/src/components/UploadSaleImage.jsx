import React, { useState } from "react";
import { apiFetch } from "../api.js";

export default function UploadSaleImage({ onDone }) {
  const [file, setFile] = useState(null);
  const [draft, setDraft] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);
  
  // Edición del draft
  const [editedAmount, setEditedAmount] = useState("");
  const [editedDatetime, setEditedDatetime] = useState("");
  const [editedCustomerName, setEditedCustomerName] = useState("");
  const [editedCustomerCuit, setEditedCustomerCuit] = useState("");
  const [editedCustomerPhone, setEditedCustomerPhone] = useState("");
  const [editedExternalRef, setEditedExternalRef] = useState("");

  async function handleFileUpload(e) {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setMsg(null);
    setFile(selectedFile);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const token = localStorage.getItem("token");
      const response = await fetch("/v1/sales/ingest", {
        method: "POST",
        body: formData,
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        try {
          const error = await response.json();
          setMsg(`Error: ${error.detail || "Error desconocido"}`);
        } catch {
          const errorText = await response.text();
          setMsg(`Error ${response.status}: ${errorText || "Error desconocido"}`);
        }
        setLoading(false);
        return;
      }

      const data = await response.json();
      if (!data || !data.draft) {
        setMsg("Error: Respuesta vacía del servidor");
        setLoading(false);
        return;
      }
      
      setDraft(data);
      
      // Prellenar formulario
      setEditedAmount(data.amount?.toString() || "");
      setEditedDatetime(data.datetime || new Date().toISOString().slice(0, 16));
      setEditedCustomerName(data.customer_name || "");
      setEditedCustomerCuit(data.customer_cuit || "");
      setEditedCustomerPhone(data.customer_phone || "");
      setEditedExternalRef(data.external_ref || "");
      
      setMsg("✓ Venta detectada desde imagen/PDF. Revisa y ajusta si es necesario.");
    } catch (e) {
      setMsg(`Error: ${e.message || "Error desconocido"}`);
    } finally {
      setLoading(false);
    }
  }

  async function saveSale() {
    setMsg(null);
    
    if (!editedAmount || isNaN(parseFloat(editedAmount))) {
      setMsg("Error: Monto requerido y debe ser un número");
      return;
    }
    
    if (!editedDatetime) {
      setMsg("Error: Fecha requerida");
      return;
    }

    try {
      const payload = {
        datetime: editedDatetime,
        amount: parseFloat(editedAmount),
        currency: "ARS",
        customer_name: editedCustomerName.trim() || null,
        customer_cuit: editedCustomerCuit.trim() || null,
        customer_phone: editedCustomerPhone.trim() || null,
        external_ref: editedExternalRef.trim() || null,
        description: null,
      };

      const data = await apiFetch("/v1/sales", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setMsg(`✓ Venta creada: #${data.id}`);
      setDraft(null);
      setFile(null);
      setEditedAmount("");
      setEditedDatetime("");
      setEditedCustomerName("");
      setEditedCustomerCuit("");
      setEditedCustomerPhone("");
      setEditedExternalRef("");
      
      onDone?.();
    } catch (e) {
      setMsg(`Error: ${e.message}`);
    }
  }

  function reset() {
    setDraft(null);
    setFile(null);
    setMsg(null);
  }

  if (!draft) {
    return (
      <div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ fontWeight: 800 }}>Subir venta (Imagen/PDF)</div>
            <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 4 }}>
              Carga un comprobante o recibo. Se extraerá automáticamente monto, fecha, nombre, etc.
            </div>
          </div>
          <span className="badge" style={{ backgroundColor: "#10b981" }}>
            OCR
          </span>
        </div>

        <div
          style={{
            marginTop: 12,
            padding: 16,
            border: "2px dashed #ccc",
            borderRadius: 6,
            textAlign: "center",
            cursor: "pointer",
            backgroundColor: "#fafafa",
            transition: "all 0.2s",
          }}
          onDragOver={(e) => {
            e.preventDefault();
            e.currentTarget.style.borderColor = "#0066cc";
            e.currentTarget.style.backgroundColor = "#f0f7ff";
          }}
          onDragLeave={(e) => {
            e.currentTarget.style.borderColor = "#ccc";
            e.currentTarget.style.backgroundColor = "#fafafa";
          }}
          onDrop={(e) => {
            e.preventDefault();
            const droppedFile = e.dataTransfer.files?.[0];
            if (droppedFile) {
              setFile(droppedFile);
              handleFileUpload({ target: { files: [droppedFile] } });
            }
          }}
        >
          <input
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileUpload}
            style={{ display: "none" }}
            id="fileInput"
          />
          <label htmlFor="fileInput" style={{ cursor: "pointer", display: "block" }}>
            {loading ? "Procesando..." : "📎 Arrastra aquí o haz clic para seleccionar"}
            {file && <div style={{ marginTop: 8, fontSize: 12 }}>📄 {file.name}</div>}
          </label>
        </div>

        {msg && (
          <div style={{ marginTop: 12, padding: 10, backgroundColor: "#fef3c7", borderRadius: 4 }}>
            {msg}
          </div>
        )}
      </div>
    );
  }

  // Mostrar formulario de edición
  return (
    <div>
      <div style={{ fontWeight: 800, marginBottom: 12 }}>Confirmar venta extraída</div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>Monto *</div>
          <input
            value={editedAmount}
            onChange={(e) => setEditedAmount(e.target.value)}
            type="number"
            step="0.01"
            required
          />
        </div>
        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>Fecha/hora (ISO) *</div>
          <input
            value={editedDatetime}
            onChange={(e) => setEditedDatetime(e.target.value)}
            type="datetime-local"
            required
          />
        </div>

        <div style={{ gridColumn: "1 / -1" }}>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>Nombre cliente</div>
          <input
            placeholder="Opcional"
            value={editedCustomerName}
            onChange={(e) => setEditedCustomerName(e.target.value)}
          />
        </div>

        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>CUIT</div>
          <input
            placeholder="Opcional"
            value={editedCustomerCuit}
            onChange={(e) => setEditedCustomerCuit(e.target.value)}
          />
        </div>

        <div>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>Teléfono</div>
          <input
            placeholder="Opcional"
            value={editedCustomerPhone}
            onChange={(e) => setEditedCustomerPhone(e.target.value)}
          />
        </div>

        <div style={{ gridColumn: "1 / -1" }}>
          <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>Referencia (pedido/ref)</div>
          <input
            placeholder="Opcional"
            value={editedExternalRef}
            onChange={(e) => setEditedExternalRef(e.target.value)}
          />
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 12 }}>
        <button className="primary" onClick={saveSale}>
          Guardar venta
        </button>
        <button
          style={{
            padding: "8px 16px",
            backgroundColor: "#f3f4f6",
            border: "1px solid #d1d5db",
            borderRadius: 4,
            cursor: "pointer",
          }}
          onClick={reset}
        >
          Cancelar
        </button>
      </div>

      {msg && (
        <div
          style={{
            marginTop: 12,
            padding: 10,
            backgroundColor: msg.includes("✓") ? "#d1fae5" : "#fef3c7",
            borderRadius: 4,
            color: msg.includes("✓") ? "#065f46" : "#92400e",
          }}
        >
          {msg}
        </div>
      )}
    </div>
  );
}
