import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api";

type Voucher = {
  id: number;
  client_id: number;
  fy: string;
  month: string;
  vtype: string;
  status: string;
  original_filename?: string;
  uploaded_at?: string;
};

const months = [
  ...Array.from({ length: 12 }, (_, i) => `2025-${String(i + 1).padStart(2, "0")}`),
  ...Array.from({ length: 12 }, (_, i) => `2026-${String(i + 1).padStart(2, "0")}`),
];

export default function UploadPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [fy, setFy] = useState("2025-26");
  const [month, setMonth] = useState(months[0]);
  const [vtype, setVtype] = useState<"PURCHASE" | "SALES" | "EXPENSE" | "BANK">("PURCHASE");
  const [file, setFile] = useState<File | null>(null);

  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [listLoading, setListLoading] = useState(false);
  const [vouchers, setVouchers] = useState<Voucher[]>([]);

  async function loadList() {
    setListLoading(true);
    try {
      const r = await api.get("/vouchers", { params: { fy, month } });
      setVouchers(r.data.vouchers || []);
    } catch {
      setVouchers([]);
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    loadList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fy, month]);

  async function upload() {
    setMsg(null);
    setErr(null);

    if (!file) {
      setErr("Please select a file first.");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("fy", fy);
      fd.append("month", month);
      fd.append("vtype", vtype);
      fd.append("file", file);

      await api.post("/vouchers/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setMsg("Uploaded successfully ✅");
      await loadList();
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  const metrics = useMemo(() => {
    const total = vouchers.length;
    const received = vouchers.filter(v => v.status === "RECEIVED").length;
    const query = vouchers.filter(v => v.status === "QUERY").length;
    const posted = vouchers.filter(v => v.status === "POSTED").length;
    return { total, received, query, posted };
  }, [vouchers]);

  return (
    <div className="space-y-6">
      <div>
        <div className="text-sm text-gray-500">Client</div>
        <div className="text-lg font-semibold">Upload Vouchers</div>
        <div className="mt-1 text-sm text-gray-500">Upload bills/invoices/statements for bookkeeping.</div>
      </div>

      <section className="rounded-xl border bg-white shadow-sm">
        <div className="border-b px-4 py-3 font-medium">Upload</div>
        <div className="p-4 space-y-4">
          <div className="grid gap-3 md:grid-cols-4">
            <label className="text-sm">
              <div className="mb-1 text-gray-600">Financial Year</div>
              <select className="w-full rounded-lg border px-3 py-2" value={fy} onChange={(e) => setFy(e.target.value)}>
                <option>2024-25</option>
                <option>2025-26</option>
              </select>
            </label>

            <label className="text-sm">
              <div className="mb-1 text-gray-600">Month</div>
              <select className="w-full rounded-lg border px-3 py-2" value={month} onChange={(e) => setMonth(e.target.value)}>
                {months.map(m => <option key={m} value={m}>{m}</option>)}
              </select>
            </label>

            <label className="text-sm">
              <div className="mb-1 text-gray-600">Voucher Category</div>
              <select className="w-full rounded-lg border px-3 py-2" value={vtype} onChange={(e) => setVtype(e.target.value as any)}>
                <option>PURCHASE</option>
                <option>SALES</option>
                <option>EXPENSE</option>
                <option>BANK</option>
              </select>
            </label>

            <label className="text-sm">
              <div className="mb-1 text-gray-600">File</div>
              <input
                ref={fileInputRef}
                className="w-full rounded-lg border px-3 py-2"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={upload}
              disabled={loading}
              className="rounded-lg bg-black px-4 py-2 text-sm text-white hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Uploading..." : "Upload"}
            </button>

            <button
              onClick={loadList}
              className="rounded-lg border bg-white px-4 py-2 text-sm hover:bg-gray-50"
            >
              Refresh List
            </button>
          </div>

          {msg && <div className="rounded-lg border bg-green-50 p-3 text-sm text-green-700">{msg}</div>}
          {err && <div className="rounded-lg border bg-red-50 p-3 text-sm text-red-700">{err}</div>}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">Total</div>
          <div className="text-2xl font-semibold">{metrics.total}</div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">Received</div>
          <div className="text-2xl font-semibold">{metrics.received}</div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">In Query</div>
          <div className="text-2xl font-semibold">{metrics.query}</div>
        </div>
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="text-sm text-gray-500">Posted</div>
          <div className="text-2xl font-semibold">{metrics.posted}</div>
        </div>
      </section>

      <section className="rounded-xl border bg-white shadow-sm overflow-hidden">
        <div className="border-b px-4 py-3 font-medium">My Uploaded Vouchers</div>

        {listLoading ? (
          <div className="p-4 text-sm text-gray-500">Loading...</div>
        ) : vouchers.length === 0 ? (
          <div className="p-4 text-sm text-gray-500">No vouchers found for selected FY/Month.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="p-3 text-left font-medium">ID</th>
                <th className="p-3 text-left font-medium">FY</th>
                <th className="p-3 text-left font-medium">Month</th>
                <th className="p-3 text-left font-medium">Type</th>
                <th className="p-3 text-left font-medium">Status</th>
                <th className="p-3 text-left font-medium">File</th>
              </tr>
            </thead>
            <tbody>
              {vouchers.map(v => (
                <tr key={v.id} className="border-t">
                  <td className="p-3 font-medium">#{v.id}</td>
                  <td className="p-3">{v.fy}</td>
                  <td className="p-3">{v.month}</td>
                  <td className="p-3">{v.vtype}</td>
                  <td className="p-3">{v.status}</td>
                  <td className="p-3 text-gray-600">{v.original_filename || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
