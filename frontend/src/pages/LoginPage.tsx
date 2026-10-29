import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("reg.admin@verischolar.demo");
  const [password, setPassword] = useState("Demo@123");
  const [error, setError] = useState("");

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      nav("/");
    } catch {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="min-h-screen grid place-items-center bg-sky">
      <form onSubmit={onSubmit} className="bg-white p-6 rounded w-96 space-y-3 shadow">
        <h2 className="text-xl font-semibold text-navy">VeriScholar Login</h2>
        <input className="w-full border p-2" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full border p-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button className="w-full bg-navy text-white py-2 rounded">Login</button>
      </form>
    </div>
  );
}
