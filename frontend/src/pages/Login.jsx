// import React, { useState } from "react";
// import { Link, useLocation, useNavigate } from "react-router-dom";
// import { Button } from "@/components/ui/button";
// import { Input } from "@/components/ui/input";
// import { Label } from "@/components/ui/label";
// import { LogIn, Mail, Lock, Loader2 } from "lucide-react";
// import AuthLayout from "@/components/AuthLayout";
// import GoogleIcon from "@/components/GoogleIcon";
// import { login } from "@/lib/api/auth";
// import { getDefaultRouteForRole, saveSession } from "@/lib/auth/session";

// export default function Login() {
//   const navigate = useNavigate();
//   const location = useLocation();
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const [error, setError] = useState("");
//   const [loading, setLoading] = useState(false);

//   const handleSubmit = async (e) => {
//     e.preventDefault();
//     setError("");
//     setLoading(true);
//     try {
//       const authResponse = await login({ email, password });
//       saveSession(authResponse);
//       const redirectTarget = getDefaultRouteForRole(authResponse?.user?.role);
//       navigate(location.state?.from || redirectTarget, { replace: true });
//     } catch (err) {
//       setError(err.message || "Invalid email or password");
//     } finally {
//       setLoading(false);
//     }
//   };

//   const handleGoogle = () => {
//     setError("Google sign-in is not connected in the current backend flow.");
//   };

//   return (
//     <AuthLayout
//       icon={LogIn}
//       title="Welcome back"
//       subtitle="Log in to your account"
//       footer={
//         <>
//           Don't have an account?{" "}
//           <Link to="/register" className="text-primary font-medium hover:underline">
//             Create one
//           </Link>
//         </>
//       }
//     >
//       {location.state?.signupSuccess && (
//         <div className="mb-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
//           {location.state.signupSuccess}
//         </div>
//       )}

//       <Button
//         variant="outline"
//         className="w-full h-12 text-sm font-medium mb-6"
//         onClick={handleGoogle}
//       >
//         <GoogleIcon className="w-5 h-5 mr-2" />
//         Continue with Google
//       </Button>

//       <div className="relative mb-6">
//         <div className="absolute inset-0 flex items-center">
//           <div className="w-full border-t border-border" />
//         </div>
//         <div className="relative flex justify-center text-xs uppercase">
//           <span className="bg-card px-3 text-muted-foreground">or</span>
//         </div>
//       </div>

//       {error && (
//         <div className="mb-4 p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
//           {error}
//         </div>
//       )}

//       <form onSubmit={handleSubmit} className="space-y-4">
//         <div className="space-y-2">
//           <Label htmlFor="email">Email</Label>
//           <div className="relative">
//             <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
//             <Input
//               id="email"
//               type="email"
//               autoComplete="email"
//               autoFocus
//               placeholder="you@example.com"
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               className="pl-10 h-12"
//               required
//             />
//           </div>
//         </div>
//         <div className="space-y-2">
//           <div className="flex items-center justify-between">
//             <Label htmlFor="password">Password</Label>
//             <Link to="/forgot-password" className="text-xs text-primary hover:underline">
//               Forgot password?
//             </Link>
//           </div>
//           <div className="relative">
//             <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" aria-hidden="true" />
//             <Input
//               id="password"
//               type="password"
//               autoComplete="current-password"
//               placeholder="••••••••"
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               className="pl-10 h-12"
//               required
//             />
//           </div>
//         </div>
//         <Button type="submit" className="w-full h-12 font-medium" disabled={loading}>
//           {loading ? (
//             <>
//               <Loader2 className="w-4 h-4 mr-2 animate-spin" />
//               Logging in...
//             </>
//           ) : (
//             "Log in"
//           )}
//         </Button>
//       </form>
//     </AuthLayout>
//   );
// }













import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import GoogleAuthButton from "@/components/auth/GoogleAuthButton";
import { useAuth } from "@/context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { passwordLogin, googleLogin, getDefaultRouteForRole } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const redirectAfterLogin = (user) => {
    const from = location.state?.from?.pathname;
    navigate(from || getDefaultRouteForRole(user?.role), { replace: true });
  };

  async function handlePasswordLogin(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await passwordLogin({ identifier, password });
      redirectAfterLogin(user);
    } catch (exc) {
      setError(exc.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleLogin(credential) {
    setError("");
    setLoading(true);
    try {
      const user = await googleLogin(credential);
      redirectAfterLogin(user);
    } catch (exc) {
      setError(exc.message || "Google login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <section className="w-full max-w-md bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
        <h1 className="text-2xl font-semibold text-slate-900">Sign in to MaatiTrace</h1>
        <p className="mt-1 text-sm text-slate-600">Use your email/phone password or Google account.</p>

        <div className="mt-6">
          <GoogleAuthButton onSuccess={handleGoogleLogin} onError={(exc) => setError(exc.message)} />
        </div>

        <div className="my-6 flex items-center gap-3 text-xs uppercase tracking-wide text-slate-400">
          <span className="h-px flex-1 bg-slate-200" />
          or
          <span className="h-px flex-1 bg-slate-200" />
        </div>

        <form onSubmit={handlePasswordLogin} className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium text-slate-700">Email or phone</span>
            <input
              value={identifier}
              onChange={(event) => setIdentifier(event.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-emerald-600"
              placeholder="name@example.com"
              autoComplete="username"
              required
            />
          </label>

          <label className="block">
            <span className="text-sm font-medium text-slate-700">Password</span>
            <input
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-emerald-600"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>

          {error ? <p className="text-sm text-red-600">{error}</p> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-emerald-700 px-4 py-2 font-medium text-white disabled:opacity-60"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-5 text-sm text-slate-600">
          New farmer?{" "}
          <Link to="/register" className="font-medium text-emerald-700">
            Create an account
          </Link>
        </p>
              </section>
    </main>
  );
}