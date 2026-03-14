import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";
import { formatLocalTime } from "../utils/date";

export default function Vitals() {
  const { patientId } = useParams();
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    if (!patientId) return;
    fetch(`${API}/patients/${patientId}/vitals?limit=100`)
      .then((r) => r.json())
      .then(setLogs)
      .catch(() => setLogs([]));
  }, [patientId]);

  return (
    <>
      <h2>Health Summary</h2>
      <p className="muted">Log of all your vital entries.</p>

      <div className="card">
        <h3>Previous vital entries</h3>
        {logs.length === 0 ? (
          <p className="muted">No entries yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {logs.map((log) => (
              <li key={log.id} style={{ padding: "0.5rem 0", borderBottom: "1px solid var(--border)" }}>
                {log.systolic_bp != null && `BP ${log.systolic_bp}/${log.diastolic_bp ?? "—"} · `}
                {log.heart_rate != null && `HR ${log.heart_rate} · `}
                {log.weight_kg != null && `Weight ${log.weight_kg} kg · `}
                {log.temperature_c != null && `Temp ${log.temperature_c}°C`}
                {log.triage_flag && (
                  <p className={log.triage_flag === "critical" ? "danger" : "warning"} style={{ margin: "0.25rem 0 0" }}>
                    {log.triage_note}
                  </p>
                )}
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
