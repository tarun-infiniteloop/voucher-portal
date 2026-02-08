import { useEffect, useMemo, useState } from "react";
import { api } from "../api";

type Client = { id: number; name: string; code: string };

export default function FirmSetupPage() {
  const [firmName, setFirmName] = useState("Demo CA Firm");
  const [firmInfo, setFirmInfo] = useState<any>(null);
  const [firmMsg, setFirmMsg] = useState<string | null>(null);

  const [clients, setClients] = useState<Client[]>([]);
  const [clientName, setClientName] = useState("Ravi Traders");
  const [clientCode, setClientCode] = useState("RAVI");
  const [clientMsg, setClientMsg] = useState<string | null>(null);

  const [clientId, setClientId] = useState<number>(1);
  const [cuEmail, setCuEmail] = useState("client1@test.com");
  const [cuName, setCuName] = useState("Ravi (Client)");
  const [cuPassword, setCuPassword] = useState("client123");
  const [cuMsg, setCuMsg] = useState<string | null>(null);

  async function refreshFirm() {
    setFirmMsg(null);
    try {
      const r = await api.get("/firm");
      setFirmInfo(r.data);
    } catch {
      setFirmInfo(null);
      setFirmMsg("Could not load firm info. Create firm first.");
    }
  }

  async function refreshClients() {
    try {
      const r = await api.get("/firm/clients");
      setClients(r.data.clients || []);
    } catch {
      setClients([]);
    }
  }

  useEffect(() => {
    refreshFirm();
    refreshClients();
  }, []);

  useEffect(() => {
    // keep a sane default for client user creation
    if (clients.length > 0) setClientId(clients[0].id);
  }, [clients]);

  const clientOptions = useMemo(() => clients.map(c => ({ label: `${c.name} (${c.code})`, value: c.id })), [clients]);

  async function createFirm() {
    setFirmMsg(null);
    try {
      await api.post("/firm", { name: firmName });
      setFirmMsg("Firm created ✅");
      await refreshFirm();
    } catch (e: any) {
      setFirmMsg(e?.response?.data?.detail || "Firm creation failed");
    }
  }

  async function createClient() {
    setClientMsg(null);
    try {
      await api.post("/firm/clients", { name: clientName, code: clientCode });
      setClientMsg("Client created ✅");
      await refreshClients();
    } catch (e: any) {
      setClientMsg(e?.response?.data?.detail || "Client creation failed");
    }
  }

  async function createClientUser() {
    setCuMsg(null);
    try {
      await api.post("/users/create-client-user", {
        client_id: Number(clientId),
        email: cuEmail,
        full_name: cuName,
        password: cuPassword,
      });
      setCuMsg("Client login created ✅");
    } catch (e: any) {
      setCuMsg(e?.response?.data?.detail || "Client user creation failed");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="text-sm text-gray-500">Admin</div>
        <div className="text-lg font-semibold">Firm Setup</div>
        <div className="mt-1 text-sm text-gray-500">
          Create firm, add clients, and create client logins.
        </div>
      </div>

      {/* 1) Create Firm */}
      <section className="rounded-xl border bg-white shadow-sm">
        <div className="border-b px-4 py-3 font-medium">1) Create Firm</div>
        <div className="p-4 space-y-3">
          <label className="block text-sm">
            <div className="mb-1 text-gray-600">Firm Name</div>
            <input
              className="w-full rounded-lg border px-3 py-2"
              value={firmName}
              onChange={(e) => setFirmName(e.target.value)}
            />
          </label>
          <div className="flex items-center gap-2">
            <button
              onClick={createFirm}
              className="rounded-lg bg-black px-4 py-2 text-sm text-white hover:opacity-90"
            >
              Create Firm
            </button>
            <button
              onClick={refreshFirm}
              className="rounded-lg border bg-white px-4 py-2 text-sm hover:bg-gray-50"
            >
              Refresh Firm Info
            </button>
          </div>

          {firmMsg && (
            <div className="rounded-lg border bg-gray-50 p-3 text-sm">{firmMsg}</div>
          )}

          {firmInfo && (
            <pre className="rounded-lg border bg-gray-50 p-3 text-xs overflow-auto">
              {JSON.stringify(firmInfo, null, 2)}
            </pre>
          )}
        </div>
      </section>

      {/* 2) Create Client */}
      <section className="rounded-xl border bg-white shadow-sm">
        <div className="border-b px-4 py-3 font-medium">2) Create Client</div>
        <div className="p-4 space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block text-sm">
              <div className="mb-1 text-gray-600">Client Name</div>
              <input
                className="w-full rounded-lg border px-3 py-2"
                value={clientName}
                onChange={(e) => setClientName(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              <div className="mb-1 text-gray-600">Client Code</div>
              <input
                className="w-full rounded-lg border px-3 py-2"
                value={clientCode}
                onChange={(e) => setClientCode(e.target.value)}
              />
            </label>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={createClient}
              className="rounded-lg bg-black px-4 py-2 text-sm text-white hover:opacity-90"
            >
              Create Client
            </button>
            <button
              onClick={refreshClients}
              className="rounded-lg border bg-white px-4 py-2 text-sm hover:bg-gray-50"
            >
              Refresh Clients
            </button>
          </div>

          {clientMsg && (
            <div className="rounded-lg border bg-gray-50 p-3 text-sm">{clientMsg}</div>
          )}

          <div className="rounded-lg border overflow-hidden">
            <div className="bg-gray-50 px-3 py-2 text-sm font-medium">Firm Clients</div>
            {clients.length === 0 ? (
              <div className="p-3 text-sm text-gray-500">No clients yet.</div>
            ) : (
              <table className="w-full text-sm">
                <thead className="text-gray-600">
                  <tr className="border-t">
                    <th className="p-2 text-left font-medium">ID</th>
                    <th className="p-2 text-left font-medium">Name</th>
                    <th className="p-2 text-left font-medium">Code</th>
                  </tr>
                </thead>
                <tbody>
                  {clients.map((c) => (
                    <tr key={c.id} className="border-t">
                      <td className="p-2">#{c.id}</td>
                      <td className="p-2">{c.name}</td>
                      <td className="p-2">{c.code}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>

      {/* 3) Create Client User */}
      <section className="rounded-xl border bg-white shadow-sm">
        <div className="border-b px-4 py-3 font-medium">3) Create Client User (login)</div>
        <div className="p-4 space-y-3">
          <div className="grid gap-3 md:grid-cols-2">
            <label className="block text-sm">
              <div className="mb-1 text-gray-600">Client</div>
              <select
                className="w-full rounded-lg border px-3 py-2"
                value={clientId}
                onChange={(e) => setClientId(Number(e.target.value))}
              >
                {clientOptions.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <div className="mb-1 text-gray-600">Client User Email</div>
              <input
                className="w-full rounded-lg border px-3 py-2"
                value={cuEmail}
                onChange={(e) => setCuEmail(e.target.value)}
              />
            </label>

            <label className="block text-sm">
              <div className="mb-1 text-gray-600">Full Name</div>
              <input
                className="w-full rounded-lg border px-3 py-2"
                value={cuName}
                onChange={(e) => setCuName(e.target.value)}
              />
            </label>

            <label className="block text-sm">
              <div className="mb-1 text-gray-600">Password</div>
              <input
                className="w-full rounded-lg border px-3 py-2"
                type="password"
                value={cuPassword}
                onChange={(e) => setCuPassword(e.target.value)}
              />
            </label>
          </div>

          <button
            onClick={createClientUser}
            className="rounded-lg bg-black px-4 py-2 text-sm text-white hover:opacity-90"
          >
            Create Client User
          </button>

          {cuMsg && (
            <div className="rounded-lg border bg-gray-50 p-3 text-sm">{cuMsg}</div>
          )}

          <div className="text-xs text-gray-500">
            After creating a client user, log out and log in using that email/password.
          </div>
        </div>
      </section>
    </div>
  );
}
