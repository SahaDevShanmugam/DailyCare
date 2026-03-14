import { useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { API } from "../App";

export default function VitalsAdd() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const [systolic, setSystolic] = useState("");
  const [diastolic, setDiastolic] = useState("");
  const [heartRate, setHeartRate] = useState("");
  const [weight, setWeight] = useState("");
  const [temp, setTemp] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = (e) => {
    e.preventDefault();
    const body = {};
    if (systolic !== "") body.systolic_bp = parseInt(systolic, 10);
    if (diastolic !== "") body.diastolic_bp = parseInt(diastolic, 10);
    if (heartRate !== "") body.heart_rate = parseInt(heartRate, 10);
    if (weight !== "") body.weight_kg = parseFloat(weight);
    if (temp !== "") body.temperature_c = parseFloat(temp);
    if (Object.keys(body).length === 0) return;
    setSubmitting(true);
    fetch(`${API}/patients/${patientId}/vitals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((r) => r.json())
      .then(() => navigate(`/patient/${patientId}/vitals`))
      .finally(() => setSubmitting(false));
  };

  return (
    <>
      <h2>Add vitals</h2>
      <p className="muted">Enter your readings. Abnormal values will be flagged.</p>

      <div className="card">
        <form onSubmit={submit}>
          <label className="label">Blood pressure (mmHg)</label>
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <input
              type="number"
              placeholder="Systolic"
              value={systolic}
              onChange={(e) => setSystolic(e.target.value)}
              min={60}
              max={250}
            />
            <span>/</span>
            <input
              type="number"
              placeholder="Diastolic"
              value={diastolic}
              onChange={(e) => setDiastolic(e.target.value)}
              min={40}
              max={150}
            />
          </div>
          <label className="label" style={{ marginTop: "0.5rem" }}>Heart rate (bpm)</label>
          <input
            type="number"
            placeholder="e.g. 72"
            value={heartRate}
            onChange={(e) => setHeartRate(e.target.value)}
            min={30}
            max={200}
          />
          <label className="label" style={{ marginTop: "0.5rem" }}>Weight (kg)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g. 75.5"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            min={20}
            max={300}
          />
          <label className="label" style={{ marginTop: "0.5rem" }}>Temperature (°C)</label>
          <input
            type="number"
            step="0.1"
            placeholder="e.g. 36.6"
            value={temp}
            onChange={(e) => setTemp(e.target.value)}
            min={35}
            max={42}
          />
          <button type="submit" disabled={submitting} style={{ marginTop: "0.75rem" }}>
            {submitting ? "Saving…" : "Save"}
          </button>
        </form>
      </div>

      <p><Link to={`/patient/${patientId}/vitals`}>← Health Summary</Link></p>
    </>
  );
}
