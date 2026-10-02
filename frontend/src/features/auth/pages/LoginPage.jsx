import { useCallback, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import AuthLayout from "@/features/auth/components/AuthLayout";
import GoogleAuthButton from "@/features/auth/components/GoogleAuthButton";
import LoginForm from "@/features/auth/components/LoginForm";
import { getDefaultRouteForRole } from "@/features/auth/authRoutes";
import { useAuth } from "@/features/auth/context/useAuth";
import { canAccess } from "@/shared/rbac/permissions";
import { useTranslation } from "@/features/i18n";

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { passwordLogin, googleLogin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { t } = useTranslation();

  const redirectAfterLogin = useCallback((user) => {
    const requestedPath = location.state?.from?.pathname;
    const destination = requestedPath && canAccess(user, requestedPath)
      ? requestedPath
      : getDefaultRouteForRole(user?.role);
    navigate(destination, { replace: true });
  }, [location.state, navigate]);

  async function handlePasswordLogin(values) {
    setLoading(true);
    setError("");
    try {
      redirectAfterLogin(await passwordLogin(values));
    } catch (requestError) {
      setError(requestError.code === "INVALID_CREDENTIALS" ? t("errors.invalidCredentials") : t("errors.loginFailed"));
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
      setError(t("errors.googleSignInFailed"));
    } finally {
      setLoading(false);
    }
  }, [googleLogin, redirectAfterLogin]);

  const handleGoogleError = useCallback((requestError) => {
    setError(t("errors.googleSignInFailed"));
  }, []);

  return (
    <AuthLayout
      title={t("auth.signIn")}
      subtitle={t("auth.useVerifiedAccount")}
      footer={<p>{t("auth.newFarmer")} <Link to="/register" className="font-semibold text-emerald-700 hover:underline">{t("auth.createAccount")}</Link></p>}
    >
      <GoogleAuthButton onSuccess={handleGoogleLogin} onError={handleGoogleError} disabled={loading} />
      <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-wide text-slate-400"><span className="h-px flex-1 bg-slate-200" />{t("auth.or")}<span className="h-px flex-1 bg-slate-200" /></div>
      <LoginForm onSubmit={handlePasswordLogin} loading={loading} error={error} />
      <div className="mt-4 flex flex-col gap-2 text-center text-sm">
        <Link to="/forgot-password" className="font-semibold text-emerald-700 hover:underline">{t("auth.forgotPassword")}</Link>
        <Link to="/request-fpo-access" className="text-slate-600 hover:underline">{t("auth.fpoAccess")}</Link>
      </div>
    </AuthLayout>
  );
}
