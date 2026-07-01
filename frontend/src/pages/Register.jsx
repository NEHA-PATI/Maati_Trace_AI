import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Loader2, Mail, Lock, UserPlus, User, Phone } from "lucide-react";
import AuthLayout from "@/components/AuthLayout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { InputOTP, InputOTPGroup, InputOTPSlot } from "@/components/ui/input-otp";
import { signup } from "@/lib/api/auth";
import { saveSession, getDefaultRouteForRole } from "@/lib/auth/session";

const DUMMY_OTP = "123565";

export default function Register() {
  const navigate = useNavigate();
  const [step, setStep] = useState("form");
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone_number: "",
    password: "",
    confirmPassword: "",
    role: "farmer",
  });
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));

  const handleFormSubmit = (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setStep("otp");
  };

  const handleVerifyAndSignup = async () => {
    setError("");
    if (otp !== DUMMY_OTP) {
      setError("Invalid OTP. Use the current launch dummy OTP.");
      return;
    }
    setLoading(true);
    try {
      const response = await signup({
        full_name: form.full_name,
        email: form.email,
        phone_number: form.phone_number || null,
        password: form.password,
        role: form.role,
      });
      saveSession(response);
      navigate(getDefaultRouteForRole(response.user.role), { replace: true });
    } catch (err) {
      setError(err?.message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  if (step === "otp") {
    return (
      <AuthLayout
        title="Verify OTP"
        subtitle={`Enter the verification code for ${form.email}`}
        icon={Mail}
        footer={
          <>
            Wrong details?{" "}
            <button type="button" onClick={() => setStep("form")} className="text-primary hover:underline">
              Go back
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            Launch dummy OTP: <span className="font-bold">{DUMMY_OTP}</span>
          </div>
          {error ? <div className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
          <div className="space-y-2">
            <Label>OTP code</Label>
            <div className="flex justify-center">
              <InputOTP maxLength={6} value={otp} onChange={setOtp}>
                <InputOTPGroup>
                  <InputOTPSlot index={0} />
                  <InputOTPSlot index={1} />
                  <InputOTPSlot index={2} />
                  <InputOTPSlot index={3} />
                  <InputOTPSlot index={4} />
                  <InputOTPSlot index={5} />
                </InputOTPGroup>
              </InputOTP>
            </div>
          </div>
          <Button type="button" className="h-12 w-full" disabled={loading || otp.length !== 6} onClick={handleVerifyAndSignup}>
            {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating account...</> : "Verify OTP and create account"}
          </Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Create account"
      subtitle="Register a MaatiTrace user with OTP verification"
      icon={UserPlus}
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-primary hover:underline">Log in</Link>
        </>
      }
    >
      <form onSubmit={handleFormSubmit} className="space-y-4">
        {error ? <div className="rounded-xl bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}
        <div className="space-y-2">
          <Label htmlFor="full_name">Full name</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input id="full_name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} className="h-12 pl-10" required />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input id="email" type="email" value={form.email} onChange={(e) => update("email", e.target.value)} className="h-12 pl-10" required />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="phone_number">Phone number</Label>
          <div className="relative">
            <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input id="phone_number" value={form.phone_number} onChange={(e) => update("phone_number", e.target.value)} className="h-12 pl-10" />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="role">Role</Label>
          <select id="role" value={form.role} onChange={(e) => update("role", e.target.value)} className="h-12 w-full rounded-md border border-input bg-background px-3 text-sm">
            <option value="farmer">Farmer</option>
            <option value="fpo">FPO</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input id="password" type="password" value={form.password} onChange={(e) => update("password", e.target.value)} className="h-12 pl-10" required />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirmPassword">Confirm password</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input id="confirmPassword" type="password" value={form.confirmPassword} onChange={(e) => update("confirmPassword", e.target.value)} className="h-12 pl-10" required />
          </div>
        </div>
        <Button type="submit" className="h-12 w-full">
          Continue to OTP
        </Button>
      </form>
    </AuthLayout>
  );
}
