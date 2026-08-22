import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./styles.css";
import { getToken } from "./api";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Parties from "./pages/Parties";
import Activities from "./pages/Activities";
import Inventory from "./pages/Inventory";
import Invoices from "./pages/Invoices";
import Proformas from "./pages/Proformas";
import Purchases from "./pages/Purchases";
import Accounting from "./pages/Accounting";
import Referrals from "./pages/Referrals";

function RequireAuth({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Dashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/customers"
          element={
            <RequireAuth>
              <Parties role="customer" />
            </RequireAuth>
          }
        />
        <Route
          path="/suppliers"
          element={
            <RequireAuth>
              <Parties role="supplier" />
            </RequireAuth>
          }
        />
        <Route
          path="/activities"
          element={
            <RequireAuth>
              <Activities />
            </RequireAuth>
          }
        />
        <Route
          path="/inventory"
          element={
            <RequireAuth>
              <Inventory />
            </RequireAuth>
          }
        />
        <Route
          path="/proformas"
          element={
            <RequireAuth>
              <Proformas />
            </RequireAuth>
          }
        />
        <Route
          path="/invoices"
          element={
            <RequireAuth>
              <Invoices />
            </RequireAuth>
          }
        />
        <Route
          path="/purchases"
          element={
            <RequireAuth>
              <Purchases />
            </RequireAuth>
          }
        />
        <Route
          path="/accounting"
          element={
            <RequireAuth>
              <Accounting />
            </RequireAuth>
          }
        />
        <Route
          path="/referrals"
          element={
            <RequireAuth>
              <Referrals />
            </RequireAuth>
          }
        />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
