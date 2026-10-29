import { FormEvent, useState } from "react";
import { api } from "../api";

export function CompliancePage() {
  const [institutionId, setInstitutionId] = useState("1");
  const [courseId, setCourseId] = useState("1");
  const [year, setYear] = useState("2026-27");
  const [result, setResult] = useState<any>(null);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const res = await api.get(`/institutions/compliance?institution_id=${institutionId}&course_id=${courseId}&academic_year=${year}`);
    setResult(res.data);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold text-navy">Compliance Monitoring</h2>
      <form onSubmit={submit} className="bg-white p-4 rounded shadow grid md:grid-cols-4 gap-2">
        <input className="border p-2" value={institutionId} onChange={(e) => setInstitutionId(e.target.value)} placeholder="Institution ID" />
        <input className="border p-2" value={courseId} onChange={(e) => setCourseId(e.target.value)} placeholder="Course ID" />
        <input className="border p-2" value={year} onChange={(e) => setYear(e.target.value)} placeholder="Academic Year" />
        <button className="bg-navy text-white rounded">Check</button>
      </form>
      {result && <pre className="bg-white p-4 rounded shadow text-sm overflow-auto">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
