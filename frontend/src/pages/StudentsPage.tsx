import { useEffect, useState } from "react";
import { api } from "../api";

export function StudentsPage() {
  const [students, setStudents] = useState<any[]>([]);

  useEffect(() => {
    api.get("/students").then((res) => setStudents(res.data));
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold text-navy">Student Records</h2>
      <div className="bg-white rounded shadow overflow-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="p-2 text-left">Internal ID</th>
              <th className="p-2 text-left">Name</th>
              <th className="p-2 text-left">Course</th>
              <th className="p-2 text-left">Year</th>
              <th className="p-2 text-left">Verification</th>
            </tr>
          </thead>
          <tbody>
            {students.map((s) => (
              <tr key={s.id} className="border-t">
                <td className="p-2">{s.internal_record_id}</td>
                <td className="p-2">{s.student_name}</td>
                <td className="p-2">{s.course_id}</td>
                <td className="p-2">{s.academic_year}</td>
                <td className="p-2">{s.verification_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
