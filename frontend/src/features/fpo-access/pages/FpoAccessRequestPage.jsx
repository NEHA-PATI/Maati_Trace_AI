import { useState } from "react";
import { Link } from "react-router-dom";

import AuthLayout from "@/features/auth/components/AuthLayout";
import { fpoAccessApi } from "@/features/fpo-access/api/fpoAccessApi";
import FpoAccessRequestForm from "@/features/fpo-access/components/FpoAccessRequestForm";

export default function FpoAccessRequestPage() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");

  async function submit(values) {
    setLoading(true);
    setError("");
    try {
      setResponse(await fpoAccessApi.submit(values));
    } catch (requestError) {
      setError(requestError.message || "The FPO access request could not be submitted.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      title="Request FPO access"
      subtitle="FPO accounts are verified and then created by an administrator through a secure invitation."
      footer={<Link to="/login" className="font-semibold text-emerald-700 hover:underline">Back to sign in</Link>}
    >
      {response ? (
        <div className="space-y-4">
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900">{response.message}</div>
          <p className="text-xs text-slate-500">Request ID: {response.request_id}</p>
        </div>
      ) : (
        <FpoAccessRequestForm onSubmit={submit} loading={loading} error={error} />
      )}
    </AuthLayout>
  );
}
