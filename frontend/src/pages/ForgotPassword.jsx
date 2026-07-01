import { Link } from "react-router-dom";

export default function ForgotPassword() {
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="max-w-md rounded-3xl border bg-card p-8">
        <h1 className="text-2xl font-black">Password reset</h1>
        <p className="mt-3 text-sm text-muted-foreground">Self-service reset is not wired yet in this gateway launch pass.</p>
        <Link to="/login" className="mt-6 inline-block text-sm font-semibold text-primary">Back to login</Link>
      </div>
    </div>
  );
}
