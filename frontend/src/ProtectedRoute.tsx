import { Navigate } from "react-router-dom";
import { useAuth } from "./auth-context";

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { me, loading } = useAuth();

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>;
  if (!me) return <Navigate to="/login" replace />;

  return children;
}
