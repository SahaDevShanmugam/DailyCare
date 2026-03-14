import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";

const MED_COLORS = ["blue", "purple", "teal"];

export default function Medications() {
  const { patientId } = useParams();
  const [meds, setMeds] = useState([]);
  const [adding, setAdding] = useState(false);
  const [addForm, setAddForm] = useState({
    name: "",
    dosage: "",
    frequency: "",
    time_of_day: "",
    instructions: "",
    conditions_not_to_take: "",
  });

  const loadMeds = () => {
    if (!patientId) return;
    fetch(`${API}/patients/${patientId}/medications`)
      .then((r) => r.json())
      .then(setMeds)
      .catch(() => setMeds([]));
  };

  useEffect(() => {
    if (!patientId) return;
    loadMeds();
  }, [patientId]);

  const submitAddMed = (e) => {
    e.preventDefault();
    if (!addForm.name.trim()) return;
    setAdding(true);
    fetch(`${API}/patients/${patientId}/medications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: addForm.name.trim(),
        dosage: addForm.dosage.trim(),
        frequency: addForm.frequency.trim(),
        time_of_day: addForm.time_of_day.trim(),
        instructions: addForm.instructions.trim(),
        conditions_not_to_take: addForm.conditions_not_to_take.trim(),
      }),
    })
      .then((r) => r.json())
      .then(() => {
        loadMeds();
        setAddForm({ name: "", dosage: "", frequency: "", time_of_day: "", instructions: "", conditions_not_to_take: "" });
      })
      .finally(() => setAdding(false));
  };

  return (
    <>
      <h2>Your medications</h2>
      <p className="muted">Add medications and view your list. Log when you take them from the home page or Recent logs.</p>

      {/* Add medication */}
      <div className="card">
        <h3>Add medication</h3>
        <form onSubmit={submitAddMed}>
          <label className="label" htmlFor="name">Medication name *</label>
          <input
            id="name"
            value={addForm.name}
            onChange={(e) => setAddForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="e.g. Furosemide"
            required
          />
          <label className="label" htmlFor="dosage" style={{ marginTop: "0.5rem" }}>Dosage</label>
          <input
            id="dosage"
            value={addForm.dosage}
            onChange={(e) => setAddForm((f) => ({ ...f, dosage: e.target.value }))}
            placeholder="e.g. 2 tabs (20 mg)"
          />
          <label className="label" htmlFor="frequency" style={{ marginTop: "0.5rem" }}>Frequency</label>
          <input
            id="frequency"
            value={addForm.frequency}
            onChange={(e) => setAddForm((f) => ({ ...f, frequency: e.target.value }))}
            placeholder="e.g. once daily, twice daily"
          />
          <label className="label" htmlFor="time_of_day" style={{ marginTop: "0.5rem" }}>Recommended time</label>
          <input
            id="time_of_day"
            value={addForm.time_of_day}
            onChange={(e) => setAddForm((f) => ({ ...f, time_of_day: e.target.value }))}
            placeholder="e.g. Morning, 08:00, After breakfast"
          />
          <label className="label" htmlFor="instructions" style={{ marginTop: "0.5rem" }}>Instructions for taking</label>
          <textarea
            id="instructions"
            value={addForm.instructions}
            onChange={(e) => setAddForm((f) => ({ ...f, instructions: e.target.value }))}
            placeholder="e.g. Take 2 tablets after every meal."
            rows={2}
          />
          <label className="label" htmlFor="conditions_not_to_take" style={{ marginTop: "0.5rem" }}>Do not take if / conditions</label>
          <textarea
            id="conditions_not_to_take"
            value={addForm.conditions_not_to_take}
            onChange={(e) => setAddForm((f) => ({ ...f, conditions_not_to_take: e.target.value }))}
            placeholder="e.g. Do not take multiple doses within 4 hours."
            rows={2}
          />
          <button type="submit" disabled={adding || !addForm.name.trim()} style={{ marginTop: "0.75rem" }}>
            {adding ? "Adding…" : "Add medication"}
          </button>
        </form>
      </div>

      {/* Medication list with instructions and conditions */}
      {meds.length > 0 && (
        <div className="card">
          <h3>Your medications</h3>
          {meds.map((m, i) => (
            <div key={m.id} style={{ marginBottom: "1rem", paddingBottom: "1rem", borderBottom: i < meds.length - 1 ? "1px solid var(--border)" : "none" }}>
              <div className="med-row" style={{ borderBottom: "none", padding: 0 }}>
                <div className={`med-bar ${MED_COLORS[i % MED_COLORS.length]}`} />
                <div style={{ flex: 1 }}>
                  <strong>{m.name}</strong> {m.dosage && ` · ${m.dosage}`} {m.frequency && ` · ${m.frequency}`}
                  {m.time_of_day && <span className="muted" style={{ display: "block" }}>At: {m.time_of_day}</span>}
                </div>
              </div>
              {m.instructions && (
                <p style={{ margin: "0.5rem 0 0 2rem", fontSize: "0.95rem" }}>
                  <strong>Instructions:</strong> {m.instructions}
                </p>
              )}
              {m.conditions_not_to_take && (
                <p style={{ margin: "0.25rem 0 0 2rem", fontSize: "0.95rem", color: "var(--warning)" }}>
                  <strong>Do not take if:</strong> {m.conditions_not_to_take}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="section-actions">
        <Link to={`/patient/${patientId}/medications/logs`} className="muted">Recent logs</Link>
      </div>

      <p><Link to={`/patient/${patientId}`}>← Back to home</Link></p>
    </>
  );
}
