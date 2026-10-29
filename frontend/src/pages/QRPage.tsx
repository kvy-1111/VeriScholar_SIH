import { FormEvent, useState } from "react";
import { api } from "../api";

export function QRPage() {
  const [studentId, setStudentId] = useState("1");
  const [created, setCreated] = useState<any>(null);
  const [verifyRef, setVerifyRef] = useState("");
  const [verified, setVerified] = useState<any>(null);

  const create = async (e: FormEvent) => {
    e.preventDefault();
    const res = await api.post("/qr/create", { student_record_id: Number(studentId) });
    setCreated(res.data);
    setVerifyRef(res.data.credential_ref);
  };

  const verify = async () => {
    const res = await api.get(`/qr/verify/${verifyRef}`);
    setVerified(res.data);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold text-navy">QR Credential Prototype</h2>
      <form onSubmit={create} className="bg-white p-4 rounded shadow space-y-2">
        <input className="border p-2 w-full" value={studentId} onChange={(e) => setStudentId(e.target.value)} placeholder="Student Record ID" />
        <button className="bg-navy text-white px-4 py-2 rounded">Create Demo Credential</button>
      </form>
      {created && <pre className="bg-white p-4 rounded text-xs overflow-auto">{JSON.stringify(created, null, 2)}</pre>}
      <div className="bg-white p-4 rounded shadow space-y-2">
        <input className="border p-2 w-full" value={verifyRef} onChange={(e) => setVerifyRef(e.target.value)} placeholder="Credential Ref" />
        <button className="bg-sky px-4 py-2 rounded" onClick={verify}>Verify Publicly</button>
      </div>
      {verified && <pre className="bg-white p-4 rounded text-xs overflow-auto">{JSON.stringify(verified, null, 2)}</pre>}
    </div>
  );
}
