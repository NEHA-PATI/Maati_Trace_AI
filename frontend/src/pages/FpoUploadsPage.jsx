import { useState } from "react";

import { environment } from "@/app/config/environment";

export default function FpoUploadsPage() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const inputStyle = {
    position: "absolute",
    width: 1,
    height: 1,
    opacity: 0,
    pointerEvents: "none",
  };

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setMessage("");
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await fetch(`${environment.apiGatewayUrl}/fpo-uploads`, {
        method: "POST",
        body,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Upload failed");
      setMessage(`${file.name} uploaded successfully.`);
      setFile(null);
      event.target.reset();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: 640, margin: "80px auto", padding: 24, fontFamily: "Arial, sans-serif" }}>
      <h1>FPO Uploads</h1>
      <p>Select a file to upload it to the FPO OneDrive folder.</p>
      <form onSubmit={upload}>
        <input
          id="fpo-file"
          type="file"
          required
          style={inputStyle}
          onChange={(event) => setFile(event.target.files[0] || null)}
        />
        <label
          htmlFor="fpo-file"
          style={{ display: "inline-block", padding: "12px 18px", background: "#2563eb", color: "white", borderRadius: 6, cursor: "pointer" }}
        >
          Choose file
        </label>
        <span style={{ marginLeft: 12 }}>{file ? file.name : "No file chosen"}</span>
        <button
          type="submit"
          disabled={!file || busy}
          style={{ display: "block", marginTop: 20, padding: "12px 18px", border: 0, borderRadius: 6, background: file && !busy ? "#16a34a" : "#9ca3af", color: "white", cursor: file && !busy ? "pointer" : "not-allowed" }}
        >
          {busy ? "Uploading…" : "Upload file"}
        </button>
      </form>
      {message && <p role="status">{message}</p>}
    </main>
  );
}
