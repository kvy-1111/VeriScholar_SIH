import { useEffect, useState } from "react";
import { api } from "../api";

export function CasesPage() {
  const [cases, setCases] = useState<any[]>([]);

  useEffect(() => {
    api.get("/cases").then((res) => setCases(res.data));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold text-navy">Investigation Cases</h2>
      <div className="grid gap-3">
        {cases.map((c) => (
          <div className="bg-white p-4 rounded shadow" key={c.id}>
            <p className="font-semibold">{c.case_ref} - {c.status}</p>
            <p className="text-sm">Risk: {c.risk_score} | Reason: {c.detection_reason}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
