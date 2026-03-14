"""Shared patient context builder for agent and daily message."""
from app.models.patient import Patient, Medication, MedicationLog, VitalsLog, SymptomLog


def format_patient_context(
    patient: Patient,
    meds: list,
    vitals_history: list,
    symptom_history: list,
    med_logs: list,
    med_id_to_name: dict,
    chat_history: list | None = None,
) -> str:
    """Build rich context so the agent can monitor and personalize from full patient data."""
    chat_history = chat_history or []
    lines = []

    lines.append("=== PATIENT & LIFESTYLE ===")
    lines.append(f"Name: {patient.name}")
    lines.append(f"Conditions: {patient.conditions or 'Not specified'}")
    lines.append(f"Medical history: {patient.medical_history or 'Not specified'}")
    lines.append(f"Diet: {patient.diet_notes or 'None'}")
    lines.append(f"Hydration: {patient.hydration_habits or 'None'}")
    lines.append(f"Smoking: {patient.smoking or 'Not specified'}")

    lines.append("")
    lines.append("=== MEDICATIONS (with clinical instructions) ===")
    if meds:
        for m in meds:
            bits = [f"- {m.name}"]
            if m.dosage:
                bits.append(f"  Dosage: {m.dosage}")
            if m.frequency:
                bits.append(f"  Frequency: {m.frequency}")
            if m.time_of_day:
                bits.append(f"  Time: {m.time_of_day}")
            if m.instructions:
                bits.append(f"  Instructions: {m.instructions}")
            if m.conditions_not_to_take:
                bits.append(f"  Do not take if: {m.conditions_not_to_take}")
            lines.append("\n".join(bits))
    else:
        lines.append("None listed.")

    lines.append("")
    lines.append("=== MEDICATION ADHERENCE (recent logs: taken / skipped) ===")
    if med_logs:
        for log in med_logs:
            name = (med_id_to_name.get(log.medication_id) or "Unknown") if log.medication_id else "General"
            status = "skipped" if log.skipped else "taken"
            date = log.taken_at.strftime("%Y-%m-%d %H:%M") if hasattr(log.taken_at, "strftime") else str(log.taken_at)
            lines.append(f"  {date}: {name} – {status}" + (f" ({log.note})" if log.note else ""))
    else:
        lines.append("No logs yet.")

    lines.append("")
    lines.append("=== VITALS HISTORY (most recent first; use for trends) ===")
    if vitals_history:
        for v in vitals_history:
            parts = []
            if v.systolic_bp is not None:
                parts.append(f"BP {v.systolic_bp}/{v.diastolic_bp or '?'}")
            if v.heart_rate is not None:
                parts.append(f"HR {v.heart_rate}")
            if v.weight_kg is not None:
                parts.append(f"Weight {v.weight_kg} kg")
            if v.temperature_c is not None:
                parts.append(f"Temp {v.temperature_c}°C")
            if parts:
                date = v.logged_at.strftime("%Y-%m-%d %H:%M") if hasattr(v.logged_at, "strftime") else str(v.logged_at)
                lines.append(f"  {date}: " + ", ".join(parts))
    else:
        lines.append("No vitals logged yet.")

    lines.append("")
    lines.append("=== SYMPTOM HISTORY (most recent first) ===")
    if symptom_history:
        for s in symptom_history:
            date = s.logged_at.strftime("%Y-%m-%d %H:%M") if hasattr(s.logged_at, "strftime") else str(s.logged_at)
            sev = f" ({s.severity})" if s.severity else ""
            lines.append(f"  {date}: {s.symptoms}{sev}")
            if s.notes:
                lines.append(f"    Note: {s.notes}")
    else:
        lines.append("No symptoms logged yet.")

    lines.append("")
    lines.append("=== RECENT CONVERSATION (use to learn habits, preferences, questions) ===")
    if chat_history:
        for msg in chat_history:
            role = "User" if msg.role == "user" else "Assistant"
            lines.append(f"  {role}: {msg.content[:500]}" + ("..." if len(msg.content) > 500 else ""))
    else:
        lines.append("No prior conversation yet.")

    return "\n".join(lines)
