import { useEffect, useState } from "react";
import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { api } from "../api";

export function DashboardPage() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.get("/analytics/dashboard").then((res) => setData(res.data));
  }, []);

  if (!data) return <p>Loading dashboard...</p>;

  const cards = data.summary;
  const chartData = [
    { name: "Records", value: cards.total_records },
    { name: "Cases", value: cards.pending_cases },
    { name: "Duplicates", value: cards.potential_duplicates },
    { name: "High Risk", value: cards.high_risk_cases },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-navy">Regulatory Dashboard</h2>
      <div className="grid md:grid-cols-3 gap-4">
        {Object.entries(cards).map(([k, v]) => (
          <div key={k} className="bg-white p-4 rounded shadow">
            <p className="text-sm text-slate-600">{k.replaceAll("_", " ")}</p>
            <p className="text-2xl font-bold text-navy">{String(v)}</p>
          </div>
        ))}
      </div>
      <div className="bg-white rounded shadow p-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Bar dataKey="value" fill="#0F2A5F" />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-sm text-slate-500">{data.note}</p>
    </div>
  );
}
