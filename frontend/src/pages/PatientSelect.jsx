import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "../App";

export default function PatientSelect() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    fetch(`${API}/patients`)
      .then((r) => r.json())
      .then(setPatients)
      .catch(() => setPatients([]))
      .finally(() => setLoading(false));
  }, []);

  const createPatient = (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    fetch(`${API}/patients`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim(), conditions: "", medical_history: "", diet_notes: "", hydration_habits: "", smoking: "" }),
    })
      .then((r) => r.json())
      .then((p) => navigate(`/patient/${p.id}`))
      .finally(() => setCreating(false));
  };

  if (loading) return <p className="muted">Loading…</p>;

  return (
    <div className="card">
      <h2>Select or add patient</h2>
      <ul style={{ listStyle: "none", padding: 0, margin: "1rem 0" }}>
        {patients.map((p) => (
          <li key={p.id} style={{ marginBottom: "0.5rem" }}>
            <button
              type="button"
              onClick={() => navigate(`/patient/${p.id}`)}
              style={{ width: "100%", textAlign: "left" }}
            >
              {p.name}
            </button>
          </li>
        ))}
      </ul>
      <form onSubmit={createPatient}>
        <label className="label" htmlFor="name">Add new patient</label>
        <input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Full name"
          autoComplete="name"
        />
        <button type="submit" disabled={creating || !name.trim()} style={{ marginTop: "0.75rem" }}>
          {creating ? "Adding…" : "Add patient"}
        </button>
      </form>
    </div>
  );
}
