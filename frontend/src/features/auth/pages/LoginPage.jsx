import { useCallback, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import AuthLayout from "@/features/auth/components/AuthLayout";
import GoogleAuthButton from "@/features/auth/components/GoogleAuthButton";
import LoginForm from "@/features/auth/components/LoginForm";
import { getDefaultRouteForRole } from "@/features/auth/authRoutes";
import { useAuth } from "@/features/auth/context/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { passwordLogin, googleLogin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const redirectAfterLogin = useCallback((user) => {
    const requestedPath = location.state?.from?.pathname;
    navigate(requestedPath || getDefaultRouteForRole(user?.role), { replace: true });
  }, [location.state, navigate]);

  async function handlePasswordLogin(values) {
    setLoading(true);
    setError("");
    try {
      redirectAfterLogin(await passwordLogin(values));
    } catch (requestError) {
      setError(requestError.message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  const handleGoogleLogin = useCallback(async (credential) => {
    setLoading(true);
    setError("");
    try {
      redirectAfterLogin(await googleLogin(credential));
    } catch (requestError) {
      setError(requestError.message || "Google sign-in failed.");
    } finally {
      setLoading(false);
    }
  }, [googleLogin, redirectAfterLogin]);

  const handleGoogleError = useCallback((requestError) => {
    setError(requestError?.message || "Google sign-in failed.");
  }, []);

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Use your verified email, Indian mobile number, or Google account."
      footer={<p>New farmer? <Link to="/register" className="font-semibold text-emerald-700 hover:underline">Create an account</Link></p>}
    >
      <GoogleAuthButton onSuccess={handleGoogleLogin} onError={handleGoogleError} disabled={loading} />
      <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-wide text-slate-400"><span className="h-px flex-1 bg-slate-200" />or<span className="h-px flex-1 bg-slate-200" /></div>
      <LoginForm onSubmit={handlePasswordLogin} loading={loading} error={error} />
      <div className="mt-4 flex flex-col gap-2 text-center text-sm">
        <Link to="/forgot-password" className="font-semibold text-emerald-700 hover:underline">Forgot password?</Link>
        <Link to="/request-fpo-access" className="text-slate-600 hover:underline">Representing an FPO? Request access</Link>
      </div>
    </AuthLayout>
  );
}
