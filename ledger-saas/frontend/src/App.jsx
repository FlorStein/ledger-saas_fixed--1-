import React, { useState } from "react";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import { getToken } from "./api.js";

export default function App() {
  const [token, setTok] = useState(getToken());
  if (!token) return <Login onLogin={() => setTok(getToken())} />;
  return <Dashboard onLogout={() => { localStorage.removeItem("token"); setTok(null); }} />;
}
