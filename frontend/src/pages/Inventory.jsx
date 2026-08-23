import React, { useEffect, useState } from "react";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import {
  TRACKING_TYPE_FA,
  UNIT_STATUS_FA,
  MOVEMENT_DIRECTION_FA,
  UNITS_OF_MEASURE,
  INVENTORY_WRITE_ROLES,
} from "../labels";

const EMPTY = {
  name: "",
  part_number: "",
  is_service: false,
  tracking_type: "serial",
  unit_of_measure: "عدد",
  base_price: "",
  specs: "",
};

export default function Inventory() {
  const { me, loading } = useMe();
  const [models, setModels] = useState([]);
  const [form, setForm] = useState(EMPTY);
  const [isCustomUnit, setIsCustomUnit] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [openId, setOpenId] = useState(null);

  const canWrite = me && INVENTORY_WRITE_ROLES.includes(me.role);

  function reload() {
    api.listProductModels().then(setModels).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (me) reload();
  }, [me]);

  async function onCreate(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api.createProductModel({
        name: form.name,
        part_number: form.part_number || null,
        is_service: form.is_service,
        // services are never serial-tracked
        tracking_type: form.is_service ? "quantity" : form.tracking_type,
        unit_of_measure: form.unit_of_measure,
        base_price: form.base_price ? Number(form.base_price) : 0,
        specs: form.specs || null,
      });
      setForm(EMPTY);
      setIsCustomUnit(false);
      reload();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>انبار — مدل‌های کالا</h2>
        <table>
          <thead>
            <tr>
              <th>شناسه</th>
              <th>نام مدل</th>
              <th>پارت‌نامبر</th>
              <th>نوع</th>
              <th>واحد شمارش</th>
              <th>قیمت پایه</th>
              <th>موجودی</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td>{m.id}</td>
                <td>{m.name}</td>
                <td>{m.part_number || "—"}</td>
                <td>{m.is_service ? "خدمت" : TRACKING_TYPE_FA[m.tracking_type]}</td>
                <td>{m.unit_of_measure}</td>
                <td>{Number(m.base_price).toLocaleString("fa-IR")}</td>
                <td>
                  {m.is_service ? (
                    <span style={{ opacity: 0.5 }}>—</span>
                  ) : (
                    <span className="badge">
                      {Number(m.current_stock).toLocaleString("fa-IR")} {m.unit_of_measure}
                    </span>
                  )}
                </td>
                <td>
                  {!m.is_service && (
                    <button
                      className="secondary"
                      style={{ width: "auto", marginTop: 0, padding: "4px 10px" }}
                      onClick={() => setOpenId(openId === m.id ? null : m.id)}
                    >
                      جزئیات
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {models.length === 0 && (
              <tr>
                <td colSpan={8} style={{ textAlign: "center", opacity: 0.6 }}>
                  موردی نیست
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {openId && (
        <ModelDetail
          key={openId}
          model={models.find((m) => m.id === openId)}
          canWrite={canWrite}
          onChanged={reload}
        />
      )}

      {canWrite && (
        <form className="card" style={{ marginTop: 20 }} onSubmit={onCreate}>
          <h2 style={{ marginTop: 0 }}>افزودن مدل کالا</h2>
          <div className="grid2">
            <div>
              <label>نام مدل *</label>
              <input
                required
                placeholder="مثلاً سوییچ سیسکو X"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </div>
            <div>
              <label>پارت‌نامبر</label>
              <input
                placeholder="مثلاً WS-C2960X-24"
                value={form.part_number}
                onChange={(e) => setForm({ ...form, part_number: e.target.value })}
              />
            </div>
            <div>
              <label>کالا یا خدمت *</label>
              <select
                value={form.is_service ? "service" : "good"}
                onChange={(e) =>
                  setForm({
                    ...form,
                    is_service: e.target.value === "service",
                    unit_of_measure:
                      e.target.value === "service" ? "خدمت" : form.unit_of_measure,
                  })
                }
              >
                <option value="good">کالا</option>
                <option value="service">خدمت</option>
              </select>
            </div>
            {!form.is_service && (
              <div>
                <label>نوع ردیابی *</label>
                <select
                  value={form.tracking_type}
                  onChange={(e) => setForm({ ...form, tracking_type: e.target.value })}
                >
                  {Object.entries(TRACKING_TYPE_FA).map(([k, v]) => (
                    <option key={k} value={k}>
                      {v}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label>واحد شمارش *</label>
              <select
                value={isCustomUnit ? "__other__" : form.unit_of_measure}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v === "__other__") {
                    setIsCustomUnit(true);
                    setForm({ ...form, unit_of_measure: "" });
                  } else {
                    setIsCustomUnit(false);
                    setForm({ ...form, unit_of_measure: v });
                  }
                }}
              >
                {UNITS_OF_MEASURE.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
                <option value="__other__">سایر (واحد دلخواه)…</option>
              </select>
              {isCustomUnit && (
                <input
                  required
                  placeholder="واحد دلخواه را بنویسید (مثلاً جفت، طاقه)"
                  value={form.unit_of_measure}
                  onChange={(e) =>
                    setForm({ ...form, unit_of_measure: e.target.value })
                  }
                  style={{ marginTop: 8 }}
                />
              )}
            </div>
            <div>
              <label>قیمت پایه</label>
              <input
                type="number"
                min="0"
                value={form.base_price}
                onChange={(e) => setForm({ ...form, base_price: e.target.value })}
              />
            </div>
            <div>
              <label>مشخصات فنی</label>
              <input
                value={form.specs}
                onChange={(e) => setForm({ ...form, specs: e.target.value })}
              />
            </div>
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={busy} style={{ width: "auto" }}>
            {busy ? "در حال ثبت…" : "ثبت مدل کالا"}
          </button>
        </form>
      )}
    </Layout>
  );
}

function ModelDetail({ model, canWrite, onChanged }) {
  if (!model) return null;
  return model.tracking_type === "serial" ? (
    <SerialUnits model={model} canWrite={canWrite} onChanged={onChanged} />
  ) : (
    <BulkMovements model={model} canWrite={canWrite} onChanged={onChanged} />
  );
}

function SerialUnits({ model, canWrite, onChanged }) {
  const [units, setUnits] = useState([]);
  const [serial, setSerial] = useState("");
  const [error, setError] = useState("");

  function reload() {
    api.listStockItems({ model_id: model.id }).then(setUnits).catch(() => {});
  }
  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model.id]);

  async function addUnit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createStockItem({ model_id: model.id, serial_number: serial });
      setSerial("");
      reload();
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  async function setStatus(id, status) {
    await api.updateStockItem(id, { status });
    reload();
    onChanged();
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <h2 style={{ marginTop: 0 }}>تک‌کالاهای «{model.name}» (سریال‌دار)</h2>
      <table>
        <thead>
          <tr>
            <th>شماره سریال</th>
            <th>وضعیت</th>
            {canWrite && <th>تغییر وضعیت</th>}
          </tr>
        </thead>
        <tbody>
          {units.map((u) => (
            <tr key={u.id}>
              <td>{u.serial_number}</td>
              <td>
                <span className="badge">{UNIT_STATUS_FA[u.status]}</span>
              </td>
              {canWrite && (
                <td>
                  <select
                    value={u.status}
                    onChange={(e) => setStatus(u.id, e.target.value)}
                    style={{ width: 150 }}
                  >
                    {Object.entries(UNIT_STATUS_FA).map(([k, v]) => (
                      <option key={k} value={k}>
                        {v}
                      </option>
                    ))}
                  </select>
                </td>
              )}
            </tr>
          ))}
          {units.length === 0 && (
            <tr>
              <td colSpan={canWrite ? 3 : 2} style={{ textAlign: "center", opacity: 0.6 }}>
                تک‌کالایی ثبت نشده
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {canWrite && (
        <form className="row" style={{ gap: 8, marginTop: 12 }} onSubmit={addUnit}>
          <input
            placeholder="شماره سریال جدید"
            value={serial}
            onChange={(e) => setSerial(e.target.value)}
            style={{ width: 240 }}
            required
          />
          <button type="submit" style={{ width: "auto", marginTop: 0 }}>
            افزودن تک‌کالا
          </button>
        </form>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}

function BulkMovements({ model, canWrite, onChanged }) {
  const [movements, setMovements] = useState([]);
  const [qty, setQty] = useState("");
  const [direction, setDirection] = useState("in");
  const [error, setError] = useState("");

  function reload() {
    api.listStockItems({ model_id: model.id }).then(setMovements).catch(() => {});
  }
  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model.id]);

  async function addMovement(e) {
    e.preventDefault();
    setError("");
    try {
      await api.createStockItem({
        model_id: model.id,
        quantity: Number(qty),
        direction,
      });
      setQty("");
      reload();
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="card" style={{ marginTop: 20 }}>
      <h2 style={{ marginTop: 0 }}>
        حرکت‌های انبار «{model.name}» (بدون سریال — {model.unit_of_measure})
      </h2>
      <table>
        <thead>
          <tr>
            <th>شناسه</th>
            <th>جهت</th>
            <th>مقدار ({model.unit_of_measure})</th>
          </tr>
        </thead>
        <tbody>
          {movements.map((mv) => (
            <tr key={mv.id}>
              <td>{mv.id}</td>
              <td>
                <span className="badge">{MOVEMENT_DIRECTION_FA[mv.direction]}</span>
              </td>
              <td>{Number(mv.quantity).toLocaleString("fa-IR")}</td>
            </tr>
          ))}
          {movements.length === 0 && (
            <tr>
              <td colSpan={3} style={{ textAlign: "center", opacity: 0.6 }}>
                حرکتی ثبت نشده
              </td>
            </tr>
          )}
        </tbody>
      </table>
      {canWrite && (
        <form className="row" style={{ gap: 8, marginTop: 12 }} onSubmit={addMovement}>
          <select value={direction} onChange={(e) => setDirection(e.target.value)} style={{ width: 120 }}>
            {Object.entries(MOVEMENT_DIRECTION_FA).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <input
            type="number"
            min="0"
            step="any"
            placeholder={`مقدار (${model.unit_of_measure})`}
            value={qty}
            onChange={(e) => setQty(e.target.value)}
            style={{ width: 180 }}
            required
          />
          <button type="submit" style={{ width: "auto", marginTop: 0 }}>
            ثبت حرکت
          </button>
        </form>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  );
}
