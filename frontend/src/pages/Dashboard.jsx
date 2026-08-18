import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useMe } from "../hooks/useMe";
import Layout from "../components/Layout";
import { ROLE_FA } from "../labels";

export default function Dashboard() {
  const { me, loading } = useMe();
  const [counts, setCounts] = useState({
    customers: null,
    suppliers: null,
    activities: null,
  });
  const [users, setUsers] = useState([]);

  useEffect(() => {
    if (!me) return;
    Promise.all([
      api.listParties({ role: "customer" }),
      api.listParties({ role: "supplier" }),
      api.listActivities(),
    ])
      .then(([customers, suppliers, activities]) =>
        setCounts({
          customers: customers.length,
          suppliers: suppliers.length,
          activities: activities.length,
        })
      )
      .catch(() => {});
    if (me.role === "manager") api.listUsers().then(setUsers).catch(() => {});
  }, [me]);

  if (loading || !me) return <div className="container">در حال بارگذاری…</div>;

  return (
    <Layout me={me}>
      <div className="card">
        <h2 style={{ marginTop: 0 }}>خوش آمدید، {me.name}</h2>
        <p style={{ opacity: 0.75 }}>
          فاز ۱ (پایه) و فاز ۲ (هسته: مشتری، فعالیت، مراحل پروژه) فعال هستند.
        </p>
        <div className="row" style={{ gap: 16, marginTop: 8 }}>
          <Link to="/customers" className="stat">
            <div className="stat-num">{counts.customers ?? "—"}</div>
            <div>مشتری‌ها</div>
          </Link>
          <Link to="/suppliers" className="stat">
            <div className="stat-num">{counts.suppliers ?? "—"}</div>
            <div>تأمین‌کننده‌ها</div>
          </Link>
          <Link to="/activities" className="stat">
            <div className="stat-num">{counts.activities ?? "—"}</div>
            <div>فعالیت‌ها</div>
          </Link>
        </div>
      </div>

      {me.role === "manager" && (
        <div className="card" style={{ marginTop: 20 }}>
          <h2 style={{ marginTop: 0 }}>کاربران تیم</h2>
          <table>
            <thead>
              <tr>
                <th>شناسه</th>
                <th>نام</th>
                <th>نقش</th>
                <th>شماره تماس</th>
                <th>وضعیت</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.name}</td>
                  <td>{ROLE_FA[u.role] || u.role}</td>
                  <td>{u.phone}</td>
                  <td>{u.is_active ? "فعال" : "غیرفعال"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Layout>
  );
}
