import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { loginWithGoogle } from "@/lib/api/auth";
import { getDefaultRouteForRole, saveSession } from "@/lib/auth/session";

const GOOGLE_SCRIPT_ID = "google-identity-services";

function loadGoogleScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }

    const existing = document.getElementById(GOOGLE_SCRIPT_ID);
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.id = GOOGLE_SCRIPT_ID;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    script.onerror = reject;

    document.head.appendChild(script);
  });
}

export default function GoogleAuthButton({ className = "" }) {
  const navigate = useNavigate();
  const buttonRef = useRef(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!clientId) {
      setError("Missing VITE_GOOGLE_CLIENT_ID in frontend .env");
      return;
    }

    let cancelled = false;

    loadGoogleScript()
      .then(() => {
        if (cancelled || !buttonRef.current) return;

        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async (response) => {
            try {
              setError("");

              const authResponse = await loginWithGoogle(response.credential);
              saveSession(authResponse);

              const redirectTarget = getDefaultRouteForRole(
                authResponse?.user?.role || "farmer",
              );

              navigate(redirectTarget, { replace: true });
            } catch (err) {
              setError(err.message || "Google login failed.");
            }
          },
        });

        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
          text: "continue_with",
          shape: "pill",
        });
      })
      .catch(() => {
        if (!cancelled) {
          setError("Unable to load Google login.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [navigate]);

  return (
    <div className={className}>
      <div ref={buttonRef} className="flex justify-center" />

      {error ? (
        <p className="mt-2 text-center text-xs text-rose-600">{error}</p>
      ) : null}
    </div>
  );
}