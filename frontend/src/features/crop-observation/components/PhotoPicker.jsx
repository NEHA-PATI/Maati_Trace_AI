import { useRef, useState } from "react";
import imageCompression from "browser-image-compression";
import { Camera, Loader2, X } from "lucide-react";

import { STRINGS, primary } from "@/features/crop-observation/i18n";

const MAX_IMAGES = 2;

/**
 * Up to 2 farmer photos per entry. Compresses on-device first — phone
 * camera photos are routinely 5–12 MB and the backend caps uploads at
 * MAX_IMAGE_BYTES (8 MB) — so a full-resolution shot is shrunk to a
 * web-friendly size before it ever leaves the phone.
 */
export default function PhotoPicker({ value = [], onChange, locale }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleFiles(event) {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;

    const room = MAX_IMAGES - value.length;
    setBusy(true);
    setError("");
    try {
      const compressed = await Promise.all(
        files.slice(0, room).map((file) =>
          imageCompression(file, {
            maxSizeMB: 1.5,
            maxWidthOrHeight: 1600,
            useWebWorker: true,
            fileType: file.type === "image/png" ? "image/png" : "image/jpeg",
          }),
        ),
      );
      onChange([...value, ...compressed.map((blob, i) => new File([blob], files[i].name, { type: blob.type }))]);
    } catch {
      setError(locale === "or-IN" ? "ଫଟୋ ପ୍ରସ୍ତୁତ କରିହେଲା ନାହିଁ।" : "Could not process that photo.");
    } finally {
      setBusy(false);
    }
  }

  function removeAt(index) {
    onChange(value.filter((_, i) => i !== index));
  }

  return (
    <div>
      <div className="text-base font-bold text-slate-900">{primary(STRINGS.addPhoto, locale)}</div>
      <div className="mt-2 flex gap-3">
        {value.map((file, index) => (
          <div key={`${file.name}-${index}`} className="relative h-20 w-20 overflow-hidden rounded-xl border border-slate-200">
            <img src={URL.createObjectURL(file)} alt="" className="h-full w-full object-cover" />
            <button
              type="button"
              onClick={() => removeAt(index)}
              className="absolute right-1 top-1 grid h-5 w-5 place-items-center rounded-full bg-black/60 text-white"
              aria-label={primary(STRINGS.delete, locale)}
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}

        {value.length < MAX_IMAGES ? (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={busy}
            className="grid h-20 w-20 place-items-center rounded-xl border-2 border-dashed border-emerald-300 bg-emerald-50 text-emerald-600 active:scale-95 disabled:opacity-60"
            aria-label={primary(STRINGS.addPhoto, locale)}
          >
            {busy ? <Loader2 className="h-6 w-6 animate-spin" /> : <Camera className="h-6 w-6" />}
          </button>
        ) : null}
      </div>
      {error ? <p className="mt-1.5 text-xs text-rose-600">{error}</p> : null}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        multiple
        className="hidden"
        onChange={handleFiles}
      />
    </div>
  );
}
