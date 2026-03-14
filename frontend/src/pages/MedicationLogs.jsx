import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";
import { formatLocalTime } from "../utils/date";

export default function MedicationLogs() {
  const { patientId } = useParams();
  const [meds, setMeds] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedMed, setSelectedMed] = useState("");
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadMeds = () => {
    if (!patientId) return;
    fetch(`${API}/patients/${patientId}/medications`)
      .then((r) => r.json())
      .then(setMeds)
      .catch(() => setMeds([]));
  };
  const loadLogs = () => {
    if (!patientId) return;
    fetch(`${API}/patients/${patientId}/medications/log?limit=50`)
      .then((r) => r.json())
      .then(setLogs)
      .catch(() => setLogs([]));
  };

  useEffect(() => {
    if (!patientId) return;
    loadMeds();
    loadLogs();
  }, [patientId]);

  const submitLog = (e) => {
    e.preventDefault();
    setSubmitting(true);
    fetch(`${API}/patients/${patientId}/medications/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        medication_id: selectedMed ? parseInt(selectedMed, 10) : null,
        skipped: false,
        note: note.trim(),
      }),
    })
      .then((r) => r.json())
      .then((newLog) => {
        setLogs((prev) => [newLog, ...prev]);
        setNote("");
        setSelectedMed("");
      })
      .finally(() => setSubmitting(false));
  };

  const medIdToName = Object.fromEntries(meds.map((m) => [m.id, m.name]));

  return (
    <>
      <h2>Log medication</h2>
      <p className="muted">Record when you take a dose. View recent logs below.</p>

      <div className="card">
        <h3>Log medication</h3>
        <form onSubmit={submitLog}>
          <label className="label" htmlFor="med">Medication (optional)</label>
          <select
            id="med"
            value={selectedMed}
            onChange={(e) => setSelectedMed(e.target.value)}
          >
            <option value="">— General log —</option>
            {meds.map((m) => (
              <option key={m.id} value={m.id}>{m.name} {m.dosage && `(${m.dosage})`}</option>
            ))}
          </select>
          <label className="label" htmlFor="note" style={{ marginTop: "0.5rem" }}>Note (optional)</label>
          <textarea id="note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. took with food" rows={2} />
          <button type="submit" disabled={submitting} style={{ marginTop: "0.75rem" }}>
            {submitting ? "Saving…" : "Save log"}
          </button>
        </form>
      </div>

      <div className="card">
        <h3>Recent logs</h3>
        {logs.length === 0 ? (
          <p className="muted">No logs yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {logs.map((log) => (
              <li key={log.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                <strong>{log.medication_id ? (medIdToName[log.medication_id] || "Unknown") : "General"}</strong>
                {" – "}
                {log.skipped ? "Skipped" : "Taken"}
                {log.note && ` – ${log.note}`}
                <span className="muted" style={{ display: "block" }}>
                  {formatLocalTime(log.taken_at)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p><Link to={`/patient/${patientId}/medications`}>← Your medications</Link></p>
    </>
  );
}
