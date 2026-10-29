import { Link, Outlet } from "react-router-dom";

const links = [
  ["Dashboard", "/"],
  ["Students", "/students"],
  ["Compliance", "/compliance"],
  ["Cases", "/cases"],
  ["Audit", "/audit"],
  ["QR", "/qr"],
];

export function Layout() {
  return (
    <div className="min-h-screen flex">
      <aside className="w-60 bg-navy text-white p-4 space-y-3">
        <h1 className="text-xl font-bold">VeriScholar</h1>
        {links.map(([label, to]) => (
          <Link className="block hover:text-sky" key={to} to={to}>{label}</Link>
        ))}
      </aside>
      <main className="flex-1 p-6 bg-slate-50">
        <Outlet />
      </main>
    </div>
  );
}
