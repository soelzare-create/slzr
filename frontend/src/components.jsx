import { useEffect, useState } from "react";
import { api, rows } from "./api";

// Modal now lives in ui.jsx (icon header, close button). Re-export for pages.
export { Modal } from "./ui.jsx";

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
