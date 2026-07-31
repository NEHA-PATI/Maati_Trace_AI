import { Link } from "react-router-dom";
import AuthLayout from "@/features/auth/components/AuthLayout";
import SignupFlow from "@/features/auth/signup/SignupFlow";

export default function RegisterPage() {
  return (
    <AuthLayout
      title="Create farmer account"
      subtitle="Verify your email now. Your detailed farmer profile is completed after sign-in."
      footer={<p>Already registered? <Link to="/login" className="font-semibold text-emerald-700 hover:underline">Sign in</Link></p>}
    >
      <SignupFlow />
    </AuthLayout>
  );
}
