import { environment } from "@/app/config/environment";
import { redactSensitive } from "@/shared/utils/sanitise";

const LEVELS = Object.freeze({ debug: 10, info: 20, warn: 30, error: 40, silent: 100 });
const configuredLevel = LEVELS[environment.logLevel] ?? LEVELS.warn;

function write(level, event, details = {}) {
  if ((LEVELS[level] ?? LEVELS.info) < configuredLevel) return;
  const payload = {
    timestamp: new Date().toISOString(),
    level,
    event,
    ...redactSensitive(details),
  };
  const method = level === "debug" ? "debug" : level === "info" ? "info" : level === "warn" ? "warn" : "error";
  console[method](JSON.stringify(payload));
}

export const logger = Object.freeze({
  debug: (event, details) => write("debug", event, details),
  info: (event, details) => write("info", event, details),
  warn: (event, details) => write("warn", event, details),
  error: (event, details) => write("error", event, details),
});
