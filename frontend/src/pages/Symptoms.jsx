import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";
import { formatLocalTime } from "../utils/date";

export default function Symptoms() {
  const { patientId } = useParams();
  const [symptoms, setSymptoms] = useState("");
  const [severity, setSeverity] = useState("");
  const [notes, setNotes] = useState("");
  const [logs, setLogs] = useState([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    fetch(`${API}/patients/${patientId}/symptoms?limit=20`)
      .then((r) => r.json())
      .then(setLogs)
      .catch(() => setLogs([]));
  }, [patientId]);

  const submit = (e) => {
    e.preventDefault();
    if (!symptoms.trim()) return;
    setSubmitting(true);
    fetch(`${API}/patients/${patientId}/symptoms`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptoms: symptoms.trim(), severity, notes: notes.trim() }),
    })
      .then((r) => r.json())
      .then((newLog) => {
        setLogs((prev) => [newLog, ...prev]);
        setSymptoms("");
        setSeverity("");
        setNotes("");
      })
      .finally(() => setSubmitting(false));
  };

  return (
    <>
      <h2>Symptom tracking</h2>
      <p className="muted">Record how you feel. If symptoms are severe or sudden, contact your care team.</p>

      <div className="card">
        <h3>Log symptoms</h3>
        <form onSubmit={submit}>
          <label className="label" htmlFor="symptoms">Symptoms *</label>
          <input
            id="symptoms"
            value={symptoms}
            onChange={(e) => setSymptoms(e.target.value)}
            placeholder="e.g. shortness of breath, swelling in legs"
            required
          />
          <label className="label" htmlFor="severity" style={{ marginTop: "0.5rem" }}>Severity</label>
          <select id="severity" value={severity} onChange={(e) => setSeverity(e.target.value)}>
            <option value="">— Select —</option>
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
          </select>
          <label className="label" htmlFor="notes" style={{ marginTop: "0.5rem" }}>Notes (optional)</label>
          <textarea id="notes" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any extra details" />
          <button type="submit" disabled={submitting || !symptoms.trim()} style={{ marginTop: "0.75rem" }}>
            {submitting ? "Saving…" : "Save"}
          </button>
        </form>
      </div>

      <div className="card">
        <h3>Recent entries</h3>
        {logs.length === 0 ? (
          <p className="muted">No entries yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {logs.map((log) => (
              <li key={log.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                <strong>{log.symptoms}</strong>
                {log.severity && ` (${log.severity})`}
                {log.notes && <p style={{ margin: "0.25rem 0 0" }}>{log.notes}</p>}
                <span className="muted" style={{ display: "block" }}>{formatLocalTime(log.logged_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p><Link to={`/patient/${patientId}`}>← Back to home</Link></p>
    </>
  );
}
