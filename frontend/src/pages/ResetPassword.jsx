import { Link } from "react-router-dom";

export default function ResetPassword() {
  return (
    <div className="grid min-h-screen place-items-center p-6">
      <div className="max-w-md rounded-3xl border bg-card p-8">
        <h1 className="text-2xl font-black">Reset password</h1>
        <p className="mt-3 text-sm text-muted-foreground">Reset-token handling is not connected in this pass. Login routing, RBAC, farm pages, and analytics are the completed launch priority.</p>
        <Link to="/login" className="mt-6 inline-block text-sm font-semibold text-primary">Back to login</Link>
      </div>
    </div>
  );
}
