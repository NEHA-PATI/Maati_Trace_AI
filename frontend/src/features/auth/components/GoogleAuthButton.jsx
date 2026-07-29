import { useEffect, useRef, useState } from "react";
import { environment } from "@/app/config/environment";

const SCRIPT_ID = "google-identity-services";

function loadGoogleIdentityServices() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) return resolve();
    const existing = document.getElementById(SCRIPT_ID);
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", reject, { once: true });
      return;
    }
    const script = document.createElement("script");
    script.id = SCRIPT_ID;
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = resolve;
    script.onerror = () => reject(new Error("Google sign-in could not be loaded."));
    document.head.appendChild(script);
  });
}

export default function GoogleAuthButton({ onSuccess, onError, disabled = false, className = "" }) {
  const buttonRef = useRef(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    if (!environment.googleClientId) {
      setLoading(false);
      onError?.(new Error("Google sign-in is not configured."));
      return undefined;
    }

    loadGoogleIdentityServices()
      .then(() => {
        if (cancelled || !buttonRef.current) return;
        window.google.accounts.id.initialize({
          client_id: environment.googleClientId,
          callback: (response) => {
            if (!response?.credential) {
              onError?.(new Error("Google did not return a credential."));
              return;
            }
            Promise.resolve(onSuccess?.(response.credential)).catch((error) => onError?.(error));
          },
        });
        buttonRef.current.replaceChildren();
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
          text: "continue_with",
          shape: "pill",
        });
        setLoading(false);
      })
      .catch((error) => {
        if (!cancelled) {
          setLoading(false);
          onError?.(error);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [onError, onSuccess]);

  return (
    <div className={className} aria-busy={loading} aria-disabled={disabled}>
      <div ref={buttonRef} className={disabled ? "pointer-events-none opacity-60" : "flex justify-center"} />
      {loading ? <p className="mt-2 text-center text-xs text-slate-500">Loading Google sign-in…</p> : null}
    </div>
  );
}
