export function getAudioDuration(file) {
  return new Promise((resolve, reject) => {
    const audio = document.createElement("audio");
    const url = URL.createObjectURL(file);
    audio.preload = "metadata";
    audio.onloadedmetadata = () => {
      const duration = Number(audio.duration);
      URL.revokeObjectURL(url);
      if (!Number.isFinite(duration)) reject(new Error("Could not read audio duration."));
      else resolve(duration);
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not read audio duration."));
    };
    audio.src = url;
  });
}
