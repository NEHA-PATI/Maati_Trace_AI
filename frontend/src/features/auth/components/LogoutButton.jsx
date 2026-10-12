import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/context/useAuth";
import LogoutConfirmModal from "./LogoutConfirmModal";

export default function LogoutButton({ allDevices = false, className = "" }) {
  const navigate = useNavigate();
  const { logout, logoutAll } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [confirmLogout, setConfirmLogout] = useState(false);

  async function handleLogout() {
    setLoading(true);
    setError("");
    try {
      if (allDevices) await logoutAll();
      else await logout();
      navigate("/login", { replace: true });
    } catch (requestError) {
      setError(requestError.message || "Server sign-out failed. Your secure session is still active.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <button type="button" onClick={() => setConfirmLogout(true)} disabled={loading} className={className}>
        {loading ? "Signing out…" : allDevices ? "Sign out all devices" : "Sign out"}
      </button>
      {error ? <span role="alert" className="max-w-xs text-xs text-rose-600">{error}</span> : null}
      <LogoutConfirmModal open={confirmLogout} loading={loading} onCancel={() => setConfirmLogout(false)} onConfirm={handleLogout} />
    </span>
  );
}
