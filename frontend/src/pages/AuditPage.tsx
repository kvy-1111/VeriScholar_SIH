import { useEffect, useState } from "react";
import { api } from "../api";

export function AuditPage() {
  const [events, setEvents] = useState<any[]>([]);

  useEffect(() => {
    api.get("/audit").then((res) => setEvents(res.data));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold text-navy">Audit Log</h2>
      <div className="bg-white rounded shadow overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100"><tr><th className="p-2">Action</th><th className="p-2">Resource</th><th className="p-2">Time</th></tr></thead>
          <tbody>
            {events.map((e) => (
              <tr key={e.id} className="border-t"><td className="p-2">{e.action}</td><td className="p-2">{e.resource_type}:{e.resource_id}</td><td className="p-2">{e.created_at}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
