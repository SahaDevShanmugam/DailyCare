import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";

const EXPORT_PASSWORD = "1234";

export default function Export() {
  const { patientId } = useParams();
  const [password, setPassword] = useState("");
  const [unlocked, setUnlocked] = useState(false);
  const [error, setError] = useState("");
  const [exportLoading, setExportLoading] = useState(false);

  const handleUnlock = (e) => {
    e.preventDefault();
    setError("");
    if (password === EXPORT_PASSWORD) {
      setUnlocked(true);
    } else {
      setError("Incorrect password. Please try again.");
    }
  };

  const handleExport = async () => {
    setExportLoading(true);
    try {
      const res = await fetch(`${API}/patients/${patientId}/export`, { cache: "no-store" });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const disp = res.headers.get("Content-Disposition");
      const match = disp && disp.match(/filename="?([^";\n]+)"?/);
      const name = match ? match[1].trim() : `patient_${patientId}_export.zip`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Export failed. Please try again.");
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Export for clinic</h2>
      <p className="muted" style={{ marginBottom: "1rem" }}>
        Export your vitals, medication logs, and symptoms as CSV files in a ZIP for your doctor or hospital.
      </p>

      {!unlocked ? (
        <form onSubmit={handleUnlock}>
          <label className="label" htmlFor="export-password">
            Enter password to continue
          </label>
          <input
            id="export-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            autoComplete="current-password"
            style={{ maxWidth: "280px", marginBottom: "0.5rem" }}
          />
          {error && <p className="danger" style={{ margin: "0 0 0.5rem" }}>{error}</p>}
          <button type="submit" className="btn" disabled={!password.trim()}>
            Unlock export
          </button>
        </form>
      ) : (
        <>
          <p className="success" style={{ marginBottom: "1rem" }}>Export unlocked.</p>
          <button
            type="button"
            className="btn"
            disabled={exportLoading}
            onClick={handleExport}
          >
            {exportLoading ? "Exporting…" : "Download ZIP for clinic"}
          </button>
        </>
      )}

      <p style={{ marginTop: "1.5rem" }}>
        <Link to={`/patient/${patientId}`}>← Back to home</Link>
      </p>
    </div>
  );
}
