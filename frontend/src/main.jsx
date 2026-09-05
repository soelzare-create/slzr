import React from "react";
import ReactDOM from "react-dom/client";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles.css";
import { AuthProvider, useAuth } from "./auth.jsx";
import Layout from "./Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Proformas from "./pages/Proformas.jsx";
import Purchases from "./pages/Purchases.jsx";
import Invoices from "./pages/Invoices.jsx";
import Parties from "./pages/Parties.jsx";
import Items from "./pages/Items.jsx";
import Accounting from "./pages/Accounting.jsx";
import Notifications from "./pages/Notifications.jsx";
import Users from "./pages/Users.jsx";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="empty">در حال بارگذاری…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/proformas" element={<Protected><Proformas /></Protected>} />
      <Route path="/purchases" element={<Protected><Purchases /></Protected>} />
      <Route path="/invoices" element={<Protected><Invoices /></Protected>} />
      <Route path="/parties" element={<Protected><Parties /></Protected>} />
      <Route path="/items" element={<Protected><Items /></Protected>} />
      <Route path="/accounting" element={<Protected><Accounting /></Protected>} />
      <Route path="/notifications" element={<Protected><Notifications /></Protected>} />
      <Route path="/users" element={<Protected><Users /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <HashRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </HashRouter>
  </React.StrictMode>
);
