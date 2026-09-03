import { useRef, useState } from "react";
import imageCompression from "browser-image-compression";
import { Loader2, X } from "lucide-react";

import { STRINGS, primary } from "@/features/crop-observation/i18n";
import { MediaCameraIcon } from "./fieldIcons";

const MAX_IMAGES = 2;

/**
 * Up to 2 farmer photos per entry. Compresses on-device first — phone
 * camera photos are routinely 5–12 MB and the backend caps uploads at
 * MAX_IMAGE_BYTES (8 MB) — so a full-resolution shot is shrunk to a
 * web-friendly size before it ever leaves the phone.
 */
export default function PhotoPicker({ value = [], onChange, locale, title, maxImages = MAX_IMAGES }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleFiles(event) {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    if (!files.length) return;

    const room = maxImages - value.length;
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
      <div className="text-sm font-bold text-[#1D2117]">{title || primary(STRINGS.addPhoto, locale)}</div>
      <div className="mt-2 flex gap-2.5 overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {Array.from({ length: maxImages }).map((_, index) => {
          const file = value[index];
          if (file) {
            return (
              <div
                key={`${file.name}-${index}`}
                className="relative h-[84px] w-[84px] shrink-0 overflow-hidden rounded-[14px] border border-[#E9E7DC]"
              >
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
            );
          }
          return (
            <button
              key={`empty-${index}`}
              type="button"
              onClick={() => inputRef.current?.click()}
              disabled={busy}
              className="flex h-[84px] w-[84px] shrink-0 flex-col items-center justify-center gap-1 rounded-[14px] border-2 border-dashed border-[#E9E7DC] bg-[#F7F8F3] text-[11px] font-bold text-[#5B6055] active:scale-[0.98] disabled:opacity-60"
              aria-label={primary(STRINGS.addPhoto, locale)}
            >
              {busy ? <Loader2 className="h-6 w-6 animate-spin" /> : <MediaCameraIcon className="h-6 w-6" />}
              <span>{primary(STRINGS.addPhoto, locale)}</span>
            </button>
          );
        })}
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
