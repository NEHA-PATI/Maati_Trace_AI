const SENSITIVE_KEY_PATTERN = /(password|token|otp|credential|secret|authorization|cookie)/i;

export function redactSensitive(value, seen = new WeakSet()) {
  if (value === null || value === undefined) return value;
  if (typeof value !== "object") return value;
  if (seen.has(value)) return "[Circular]";
  seen.add(value);

  if (Array.isArray(value)) {
    return value.map((item) => redactSensitive(item, seen));
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key,
      SENSITIVE_KEY_PATTERN.test(key) ? "[REDACTED]" : redactSensitive(item, seen),
    ]),
  );
}

export function maskEmail(email) {
  const [local = "", domain = ""] = String(email || "").split("@");
  if (!domain) return "";
  const visible = local.slice(0, Math.min(2, local.length));
  return `${visible}${"*".repeat(Math.max(2, local.length - visible.length))}@${domain}`;
}
