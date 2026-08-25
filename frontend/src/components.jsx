import { useEffect, useState } from "react";
import { api, rows } from "./api";

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" style={wide ? { width: 820 } : undefined} onClick={(e) => e.stopPropagation()}>
        <div className="toolbar">
          <h2>{title}</h2>
          <button className="btn sm" onClick={onClose}>بستن</button>
        </div>
        {children}
      </div>
    </div>
  );
}

const PROFORMA_BADGE = {
  DRAFT: "gray", CONFIRMED: "blue", AWAITING_PURCHASE: "amber",
  READY: "green", INVOICED: "green", CANCELLED: "red", UNFULFILLABLE: "red",
};
const INVOICE_BADGE = { ISSUED: "green", CANCELLED: "red", RETURNED: "amber" };
const PURCHASE_BADGE = { DRAFT: "gray", REGISTERED: "green", CANCELLED: "red" };

export function StatusBadge({ status, display, kind = "proforma" }) {
  const map = kind === "invoice" ? INVOICE_BADGE : kind === "purchase" ? PURCHASE_BADGE : PROFORMA_BADGE;
  return <span className={`badge ${map[status] || "gray"}`}>{display || status}</span>;
}

// Hook: load a list endpoint with reload support.
export function useList(path) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  function reload() {
    setLoading(true);
    api.get(path)
      .then((d) => setData(rows(d)))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }
  useEffect(() => { reload(); }, [path]);
  return { data, loading, error, reload, setError };
}

// Options loader for a <select>.
export function useOptions(path) {
  const [opts, setOpts] = useState([]);
  useEffect(() => { api.get(path).then((d) => setOpts(rows(d))).catch(() => {}); }, [path]);
  return opts;
}
