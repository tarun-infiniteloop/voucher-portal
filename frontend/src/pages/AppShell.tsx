import { NavLink, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth-context";

import DashboardPage from "./DashboardPage";
import InboxPage from "./InboxPage";
import UploadPage from "./UploadPage";
import FirmSetupPage from "./FirmSetupPage";

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "block rounded-lg px-3 py-2 text-sm",
          isActive ? "bg-black text-white" : "text-gray-700 hover:bg-gray-100",
        ].join(" ")
      }
    >
      {label}
    </NavLink>
  );
}

export default function AppShell() {
  const { me, logout } = useAuth();
  const role = me?.role;
  const location = useLocation();

  const title =
    location.pathname.includes("/firm")
      ? "Firm Setup"
      : location.pathname.includes("/inbox")
        ? "Review & Export"
        : location.pathname.includes("/upload")
          ? "Upload Vouchers"
          : "Dashboard";

  const isAdmin = role === "CA_ADMIN" || role === "ADMIN" || role === "CA";
  const isClient = role === "CLIENT";

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-72 border-r bg-white min-h-screen flex flex-col">
          <div className="p-4">
            <div className="text-lg font-semibold">Voucher Portal</div>
            <div className="mt-1 text-xs text-gray-500">
              {me?.full_name} · {me?.role}
            </div>
          </div>

          <div className="px-2 pb-2 space-y-1">
            <NavItem to="/app/dashboard" label="Dashboard" />

            {isAdmin && <NavItem to="/app/firm" label="Firm Setup" />}
            {isClient && <NavItem to="/app/upload" label="Upload Vouchers" />}
            {!isClient && <NavItem to="/app/inbox" label="Review & Export" />}
          </div>

          <div className="mt-auto p-4">
            <button
              onClick={logout}
              className="w-full rounded-lg border bg-white px-3 py-2 text-sm hover:bg-gray-50"
            >
              Logout
            </button>
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1">
          {/* Topbar */}
          <div className="h-14 border-b bg-white px-6 flex items-center justify-between">
            <div className="text-base font-medium">{title}</div>
          </div>

          {/* Page content */}
          <div className="p-6">
            <Routes>
              <Route path="/" element={<Navigate to="/app/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Admin */}
              {isAdmin && <Route path="/firm" element={<FirmSetupPage />} />}

              {/* Client */}
              {isClient && <Route path="/upload" element={<UploadPage />} />}

              {/* CA/Admin */}
              {!isClient && <Route path="/inbox" element={<InboxPage />} />}

              <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  );
}
