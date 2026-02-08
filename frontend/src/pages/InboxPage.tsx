import { useEffect, useMemo, useState } from "react";
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

type CommentRow = {
  id?: number;
  user_id?: number;
  message: string;
  created_at?: string;
};

type VoucherDetailPayload = {
  voucher: Voucher;
  comments?: CommentRow[];
};

const STATUS_LABEL: Record<string, string> = {
  RECEIVED: "Pending Review",
  QUERY: "Client Clarification",
  POSTED: "Posted",
};

function Badge({ status }: { status: string }) {
  const label = STATUS_LABEL[status] || status;
  const cls =
    status === "POSTED"
      ? "bg-green-50 text-green-700 border-green-200"
      : status === "QUERY"
        ? "bg-amber-50 text-amber-700 border-amber-200"
        : "bg-blue-50 text-blue-700 border-blue-200";

  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${cls}`}>
      {label}
    </span>
  );
}

function guessMime(filename?: string) {
  const f = (filename || "").toLowerCase();
  if (f.endsWith(".pdf")) return "application/pdf";
  if (f.endsWith(".png")) return "image/png";
  if (f.endsWith(".jpg") || f.endsWith(".jpeg")) return "image/jpeg";
  return "application/octet-stream";
}

export default function InboxPage() {
  // list
  const [loading, setLoading] = useState(true);
  const [vouchers, setVouchers] = useState<Voucher[]>([]);
  const [err, setErr] = useState<string | null>(null);

  // detail
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<VoucherDetailPayload | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // comment compose
  const [newComment, setNewComment] = useState("");
  const [sendingComment, setSendingComment] = useState(false);

  // status update
  const [newStatus, setNewStatus] = useState<"RECEIVED" | "QUERY" | "POSTED">("POSTED");
  const [updatingStatus, setUpdatingStatus] = useState(false);

  // file preview
  const [fileLoading, setFileLoading] = useState(false);
  const [fileErr, setFileErr] = useState<string | null>(null);
  const [fileBlobUrl, setFileBlobUrl] = useState<string | null>(null);
  const [fileMime, setFileMime] = useState<string | null>(null);

  // cleanup blob URL on change/unmount
  useEffect(() => {
    return () => {
      if (fileBlobUrl) URL.revokeObjectURL(fileBlobUrl);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function clearFilePreview() {
    setFileErr(null);
    setFileMime(null);
    setFileLoading(false);
    if (fileBlobUrl) URL.revokeObjectURL(fileBlobUrl);
    setFileBlobUrl(null);
  }

  async function loadList() {
    setLoading(true);
    setErr(null);
    try {
      const r = await api.get("/vouchers");
      const rows: Voucher[] = r.data.vouchers || [];
      setVouchers(rows);

      if (!selectedId && rows.length > 0) {
        void loadDetail(rows[0].id);
      }
    } catch {
      setErr("Failed to load vouchers");
      setVouchers([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadDetail(id: number) {
    clearFilePreview();
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const r = await api.get(`/vouchers/by-id/${id}`);
      const payload: VoucherDetailPayload = r.data;
      setDetail(payload);

      const s = (payload?.voucher?.status || "RECEIVED") as any;
      if (s === "RECEIVED" || s === "QUERY" || s === "POSTED") setNewStatus(s);
    } catch {
      setDetail(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function sendComment() {
    if (!selectedId) return;
    const msg = newComment.trim();
    if (!msg) return;

    setSendingComment(true);
    try {
      await api.post(`/vouchers/${selectedId}/comment`, { message: msg });
      setNewComment("");
      await loadDetail(selectedId);
      await loadList();
    } finally {
      setSendingComment(false);
    }
  }

  async function updateStatus() {
    if (!selectedId) return;

    setUpdatingStatus(true);
    try {
      await api.patch(`/vouchers/${selectedId}/status`, { status: newStatus });
      await loadDetail(selectedId);
      await loadList();
    } finally {
      setUpdatingStatus(false);
    }
  }

    async function loadFilePreview() {
    if (!selectedId || !detail?.voucher) return;

    clearFilePreview();
    setFileLoading(true);
    setFileErr(null);

    try {
        const filename = detail.voucher.original_filename || `voucher_${selectedId}`;
        const guessed = guessMime(filename);

        const res = await api.get(`/vouchers/${selectedId}/file`, {
        responseType: "arraybuffer", // IMPORTANT: more reliable than blob here
        });

        const buf = res.data as ArrayBuffer;
        if (!buf || buf.byteLength === 0) {
        setFileErr("File is empty (0 bytes). Check backend / stored file path.");
        return;
        }

        const blob = new Blob([buf], { type: guessed });
        const url = URL.createObjectURL(blob);

        setFileMime(guessed);
        setFileBlobUrl(url);
    } catch (e: any) {
        setFileErr("Failed to load file preview");
    } finally {
        setFileLoading(false);
    }
    }


  function downloadFile() {
    if (!fileBlobUrl || !detail?.voucher) return;
    const a = document.createElement("a");
    a.href = fileBlobUrl;
    a.download = detail.voucher.original_filename || `voucher_${detail.voucher.id}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  useEffect(() => {
    loadList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedVoucher = detail?.voucher;
  const comments = detail?.comments || [];

  const metrics = useMemo(() => {
    const total = vouchers.length;
    const received = vouchers.filter((v) => v.status === "RECEIVED").length;
    const query = vouchers.filter((v) => v.status === "QUERY").length;
    const posted = vouchers.filter((v) => v.status === "POSTED").length;
    return { total, received, query, posted };
  }, [vouchers]);

  const isPdf = fileMime === "application/pdf" || (selectedVoucher?.original_filename || "").toLowerCase().endsWith(".pdf");
  const isImage =
    (fileMime || "").startsWith("image/") ||
    /\.(png|jpg|jpeg)$/i.test(selectedVoucher?.original_filename || "");

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="text-sm text-gray-500">Client Voucher Inbox</div>
          <div className="text-lg font-semibold">Review & Export</div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={loadList}
            className="rounded-lg border bg-white px-3 py-2 text-sm hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* quick metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-xl border bg-white p-3 shadow-sm">
          <div className="text-xs text-gray-500">Total</div>
          <div className="text-xl font-semibold">{metrics.total}</div>
        </div>
        <div className="rounded-xl border bg-white p-3 shadow-sm">
          <div className="text-xs text-gray-500">Received</div>
          <div className="text-xl font-semibold">{metrics.received}</div>
        </div>
        <div className="rounded-xl border bg-white p-3 shadow-sm">
          <div className="text-xs text-gray-500">In Query</div>
          <div className="text-xl font-semibold">{metrics.query}</div>
        </div>
        <div className="rounded-xl border bg-white p-3 shadow-sm">
          <div className="text-xs text-gray-500">Posted</div>
          <div className="text-xl font-semibold">{metrics.posted}</div>
        </div>
      </div>

      {err && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {err}
        </div>
      )}

      {/* Main: table + detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Left: table */}
        <div className="lg:col-span-2 rounded-xl border bg-white shadow-sm overflow-hidden">
          {loading ? (
            <div className="p-4 text-sm text-gray-500">Loading...</div>
          ) : vouchers.length === 0 ? (
            <div className="p-4 text-sm text-gray-500">No vouchers found.</div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="text-left font-medium p-3">ID</th>
                  <th className="text-left font-medium p-3">Client</th>
                  <th className="text-left font-medium p-3">FY</th>
                  <th className="text-left font-medium p-3">Month</th>
                  <th className="text-left font-medium p-3">Type</th>
                  <th className="text-left font-medium p-3">Status</th>
                  <th className="text-left font-medium p-3">File</th>
                </tr>
              </thead>
              <tbody>
                {vouchers.map((v) => (
                  <tr
                    key={v.id}
                    className={`border-t hover:bg-gray-50 cursor-pointer ${
                      selectedId === v.id ? "bg-gray-50" : ""
                    }`}
                    onClick={() => loadDetail(v.id)}
                  >
                    <td className="p-3 font-medium">#{v.id}</td>
                    <td className="p-3">{v.client_id}</td>
                    <td className="p-3">{v.fy}</td>
                    <td className="p-3">{v.month}</td>
                    <td className="p-3">{v.vtype}</td>
                    <td className="p-3">
                      <Badge status={v.status} />
                    </td>
                    <td className="p-3 text-gray-600">{v.original_filename || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Right: detail panel */}
        <div className="rounded-xl border bg-white shadow-sm p-4">
          {!selectedId ? (
            <div className="text-sm text-gray-500">Select a voucher to review.</div>
          ) : detailLoading ? (
            <div className="text-sm text-gray-500">Loading voucher...</div>
          ) : !detail || !selectedVoucher ? (
            <div className="text-sm text-gray-500">Could not load voucher details.</div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="text-sm text-gray-500">Voucher Detail</div>
                <div className="flex items-center justify-between">
                  <div className="text-lg font-semibold">Voucher #{selectedVoucher.id}</div>
                  <Badge status={selectedVoucher.status} />
                </div>
              </div>

              <div className="text-sm space-y-1">
                <div>
                  <span className="text-gray-500">Client:</span> {selectedVoucher.client_id}
                </div>
                <div>
                  <span className="text-gray-500">FY/Month:</span> {selectedVoucher.fy} / {selectedVoucher.month}
                </div>
                <div>
                  <span className="text-gray-500">Type:</span> {selectedVoucher.vtype}
                </div>
                <div>
                  <span className="text-gray-500">File:</span> {selectedVoucher.original_filename || "-"}
                </div>
              </div>

              {/* File preview */}
              <div className="rounded-xl border p-3 bg-white space-y-2">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">Voucher File</div>
                  <div className="flex gap-2">
                    <button
                      onClick={loadFilePreview}
                      disabled={fileLoading}
                      className="h-9 rounded-md border bg-white px-3 text-sm hover:bg-gray-50 disabled:opacity-60"
                    >
                      {fileLoading ? "Loading..." : "Load Preview"}
                    </button>
                    <button
                      onClick={downloadFile}
                      disabled={!fileBlobUrl}
                      className="h-9 rounded-md bg-black px-3 text-sm font-medium text-white hover:bg-gray-900 disabled:opacity-60"
                    >
                      Download
                    </button>
                  </div>
                </div>

                {fileErr && (
                  <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                    {fileErr}
                  </div>
                )}

                {!fileBlobUrl ? (
                  <div className="text-xs text-gray-500">
                    Click <b>Load Preview</b> to view PDF/image.
                  </div>
                ) : isPdf ? (
                  <iframe
                    title="voucher-pdf"
                    src={fileBlobUrl}
                    className="w-full h-[420px] rounded-lg border"
                  />
                ) : isImage ? (
                  <img
                    src={fileBlobUrl}
                    alt="voucher"
                    className="w-full rounded-lg border"
                  />
                ) : (
                  <div className="text-sm text-gray-600">
                    Preview not supported for this file type. Use Download.
                  </div>
                )}
              </div>

              {/* Status update */}
              <div className="rounded-xl border p-3 bg-white">
                <div className="text-sm font-medium mb-2">Status</div>
                <div className="flex gap-2">
                  <select
                    value={newStatus}
                    onChange={(e) => setNewStatus(e.target.value as any)}
                    className="h-10 flex-1 rounded-md border border-gray-300 px-3 text-sm outline-none focus:ring-2 focus:ring-black"
                  >
                    <option value="RECEIVED">RECEIVED</option>
                    <option value="QUERY">QUERY</option>
                    <option value="POSTED">POSTED</option>
                  </select>

                  <button
                    onClick={updateStatus}
                    disabled={updatingStatus}
                    className="h-10 rounded-md bg-black px-3 text-sm font-medium text-white hover:bg-gray-900 disabled:opacity-60"
                  >
                    {updatingStatus ? "Updating..." : "Update"}
                  </button>
                </div>
              </div>

              {/* Comments */}
              <div className="pt-2 border-t">
                <div className="text-sm font-medium mb-2">Comments</div>

                {comments.length ? (
                  <div className="space-y-2 max-h-64 overflow-auto pr-1">
                    {comments.map((c) => (
                      <div
                        key={c.id ?? `${c.user_id}-${c.created_at}-${c.message.slice(0, 8)}`}
                        className="rounded-lg border bg-white p-2"
                      >
                        <div className="text-xs text-gray-500">
                          User {c.user_id ?? "-"} · {c.created_at ?? "-"}
                        </div>
                        <div className="text-sm whitespace-pre-wrap">{c.message}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-gray-500">No comments yet.</div>
                )}

                <div className="mt-3 grid gap-2">
                  <textarea
                    className="min-h-[90px] w-full rounded-md border border-gray-300 p-2 text-sm outline-none focus:ring-2 focus:ring-black"
                    placeholder="Ask client for clarification..."
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                  />

                  <button
                    onClick={sendComment}
                    disabled={sendingComment || !newComment.trim()}
                    className="h-10 rounded-md bg-black text-white text-sm font-medium hover:bg-gray-900 disabled:opacity-60"
                  >
                    {sendingComment ? "Sending..." : "Send Comment"}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
