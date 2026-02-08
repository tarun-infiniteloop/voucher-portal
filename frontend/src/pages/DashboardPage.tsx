import { useEffect, useState } from "react";
import { api } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState<any[]>([]);

  useEffect(() => {
    api.get("/reports/stats")
      .then(r => setStats(r.data.summary || []))
      .catch(() => setStats([]));
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-4">
      {stats.map((row) => (
        <div key={row.vtype} className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">{row.vtype}</div>
          <div className="text-2xl font-semibold">{row.total}</div>
        </div>
      ))}
      {stats.length === 0 && (
        <div className="text-sm text-gray-500">No stats yet.</div>
      )}
    </div>
  );
}
