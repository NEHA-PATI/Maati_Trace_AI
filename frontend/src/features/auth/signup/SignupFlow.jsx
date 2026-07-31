import { useMemo, useState } from "react";

import { environment } from "@/app/config/environment";
import { authApi } from "@/features/auth/api/authApi";
import { useAuth } from "@/features/auth/context/useAuth";
import AccountStep from "@/features/auth/signup/AccountStep";
import SignupCompleteStep from "@/features/auth/signup/SignupCompleteStep";
import VerifyOtpStep from "@/features/auth/signup/VerifyOtpStep";
import { logger } from "@/shared/logging/logger";

const INITIAL_ACCOUNT = {
  full_name: "",
  email: "",
  phone_number: "",
  password: "",
  confirm_password: "",
  consent_terms: false,
};

function accountFingerprint(value) {
  return JSON.stringify({
    full_name: value.full_name,
    email: value.email,
    phone_number: value.phone_number,
    password: value.password,
    consent_terms: value.consent_terms,
  });
}

function signupPayload(value) {
  return {
    full_name: value.full_name,
    email: value.email,
    phone_number: value.phone_number,
    password: value.password,
    consent_terms: value.consent_terms,
  };
}

export default function SignupFlow() {
  const { adoptAuthResponse } = useAuth();
  const [step, setStep] = useState("account");
  const [draft, setDraft] = useState(INITIAL_ACCOUNT);
  const [submittedFingerprint, setSubmittedFingerprint] = useState("");
  const [signupSessionId, setSignupSessionId] = useState("");
  const [maskedEmail, setMaskedEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [expiresAt, setExpiresAt] = useState(0);
  const [resendAvailableAt, setResendAvailableAt] = useState(0);
  const [resendsRemaining, setResendsRemaining] = useState(environment.otpMaxResends);
  const [completedUser, setCompletedUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const stepNumber = useMemo(() => ({ account: 1, verify: 2, complete: 3 })[step], [step]);

  async function handleAccountContinue(values) {
    setError("");
    setDraft(values);
    const nextFingerprint = accountFingerprint(values);

    if (signupSessionId && nextFingerprint === submittedFingerprint) {
      setStep("verify");
      return;
    }

    setLoading(true);
    try {
      if (signupSessionId) {
        await authApi.cancelSignup(signupSessionId, "user_changed_details");
        setSignupSessionId("");
        setOtp("");
      }
      const response = await authApi.startSignup(signupPayload(values));
      setSignupSessionId(response.signup_session_id);
      setSubmittedFingerprint(nextFingerprint);
      setMaskedEmail(response.masked_email);
      setExpiresAt(Date.now() + response.expires_in_seconds * 1000);
      setResendAvailableAt(Date.now() + response.resend_available_in_seconds * 1000);
      setResendsRemaining(environment.otpMaxResends);
      setOtp("");
      setStep("verify");
      logger.info("signup_otp_requested", { signupSessionId: response.signup_session_id });
    } catch (requestError) {
      setError(requestError.message || "Signup could not be started.");
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setLoading(true);
    setError("");
    try {
      const response = await authApi.resendSignupOtp(signupSessionId);
      setOtp("");
      setExpiresAt(Date.now() + response.expires_in_seconds * 1000);
      setResendAvailableAt(Date.now() + response.resend_available_in_seconds * 1000);
      setResendsRemaining(response.resends_remaining);
      logger.info("signup_otp_resent", { signupSessionId });
    } catch (requestError) {
      setError(requestError.message || "A new code could not be sent.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRestart() {
    setLoading(true);
    setError("");
    try {
      if (signupSessionId) await authApi.cancelSignup(signupSessionId, "otp_resend_limit_reached");
    } catch (requestError) {
      logger.warn("signup_restart_cancel_failed", {
        code: requestError?.code,
        status: requestError?.status,
        correlationId: requestError?.correlationId,
      });
    } finally {
      setSignupSessionId("");
      setSubmittedFingerprint("");
      setOtp("");
      setExpiresAt(0);
      setResendAvailableAt(0);
      setResendsRemaining(environment.otpMaxResends);
      setStep("account");
      setLoading(false);
    }
  }

  async function handleVerify() {
    setLoading(true);
    setError("");
    try {
      await authApi.verifySignupOtp(signupSessionId, otp);
      const authResponse = await authApi.completeSignup(signupSessionId);
      const user = adoptAuthResponse(authResponse);
      setCompletedUser(user);
      setStep("complete");
      setOtp("");
    } catch (requestError) {
      setError(requestError.message || "The code could not be verified.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center gap-2" aria-label={`Signup step ${stepNumber} of 3`}>
        {[1, 2, 3].map((item) => <span key={item} className={`h-2 flex-1 rounded-full ${item <= stepNumber ? "bg-emerald-600" : "bg-slate-200"}`} />)}
      </div>

      {step === "account" ? (
        <AccountStep defaultValues={draft} onContinue={handleAccountContinue} loading={loading} error={error} />
      ) : null}
      {step === "verify" ? (
        <VerifyOtpStep
          maskedEmail={maskedEmail}
          otp={otp}
          onOtpChange={setOtp}
          onVerify={handleVerify}
          onResend={handleResend}
          onBack={() => { setError(""); setStep("account"); }}
          onRestart={handleRestart}
          loading={loading}
          error={error}
          expiresAt={expiresAt}
          resendAvailableAt={resendAvailableAt}
          resendsRemaining={resendsRemaining}
        />
      ) : null}
      {step === "complete" ? <SignupCompleteStep user={completedUser} /> : null}
    </div>
  );
}
