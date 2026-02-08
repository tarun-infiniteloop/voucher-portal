import { useEffect, useState } from "react";
import { api, setAuthToken } from "./api";
import { saveToken, getToken, clearToken } from "./auth";

export default function App() {
  const [email, setEmail] = useState("admin@cadsk.local");
  const [password, setPassword] = useState("admin123");
  const [me, setMe] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadMe() {
    try {
      const r = await api.get("/auth/me");
      setMe(r.data);
    } catch {
      clearToken();
      setMe(null);
    } finally {
      setLoading(false);
    }
  }

  async function login() {
    setErr(null);
    try {
      const r = await api.post("/auth/login", { email, password });
      const token = r.data.access_token;
      saveToken(token);
      setAuthToken(token);
      await loadMe();
    } catch (e: any) {
      setErr("Login failed");
    }
  }

  function logout() {
    clearToken();
    setAuthToken(null);
    setMe(null);
  }

  // Auto login on refresh
  useEffect(() => {
    const token = getToken();
    if (token) {
      setAuthToken(token);
      loadMe();
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

  return (
  <div className="p-10">
    <h1 className="text-4xl font-bold text-blue-600">
      Tailwind Working 🚀
    </h1>
  </div>
);

//   return (
//     <div style={{ padding: 24 }}>
//       <h2>Voucher Portal (React)</h2>

//       {!me ? (
//         <div style={{ display: "grid", gap: 8, maxWidth: 300 }}>
//           <input value={email} onChange={(e) => setEmail(e.target.value)} />
//           <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
//           <button onClick={login}>Login</button>
//           {err && <div style={{ color: "red" }}>{err}</div>}
//         </div>
//       ) : (
//         <div>
//           <button onClick={logout}>Logout</button>

//           <h3>Welcome {me.full_name}</h3>
//           <p>Role: {me.role}</p>

//           <pre>{JSON.stringify(me, null, 2)}</pre>
//         </div>
//       )}
//     </div>
//   );
// }
