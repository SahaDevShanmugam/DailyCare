import csv
import io
import zipfile
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, asc
from app.config import get_settings
from app.database import get_db
from app.models.patient import Patient, VitalsLog, Medication, MedicationLog, SymptomLog, ChatMessage
from app.schemas.patient import PatientCreate, PatientUpdate, PatientRead
from app.services.agent import get_daily_message
from app.utils.patient_context import format_patient_context
from app.ml.risk_score import compute_risk
from app.triage.vitals import triage_vitals

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=PatientRead)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = Patient(
        name=data.name,
        age=data.age,
        sex=data.sex,
        conditions=data.conditions or "",
        medical_history=data.medical_history or "",
        diet_notes=data.diet_notes or "",
        hydration_habits=data.hydration_habits or "",
        smoking=data.smoking or "",
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/", response_model=list[PatientRead])
async def list_patients(db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Patient).order_by(Patient.id))
    return list(r.scalars().all())


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    return patient


@router.get("/{patient_id}/export")
async def export_patient_logs(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Export patient info and all logs (vitals, medication consumption, symptoms) as a ZIP of CSVs for clinics/hospitals."""
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")

    vitals_r = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.patient_id == patient_id)
        .order_by(asc(VitalsLog.logged_at))
    )
    vitals = list(vitals_r.scalars().all())

    meds_r = await db.execute(select(Medication).where(Medication.patient_id == patient_id))
    meds = list(meds_r.scalars().all())
    med_id_to_info = {m.id: {"name": m.name, "dosage": m.dosage or "", "frequency": m.frequency or ""} for m in meds}

    med_logs_r = await db.execute(
        select(MedicationLog)
        .where(MedicationLog.patient_id == patient_id)
        .order_by(asc(MedicationLog.taken_at))
    )
    med_logs = list(med_logs_r.scalars().all())

    symptoms_r = await db.execute(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient_id)
        .order_by(asc(SymptomLog.logged_at))
    )
    symptoms = list(symptoms_r.scalars().all())

    export_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in (patient.name or "patient"))[:50].strip() or "patient"
    zip_filename = f"patient_{patient_id}_{safe_name}_export_{export_date}.zip"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # patient_info.csv
        bio = io.StringIO()
        w = csv.writer(bio)
        w.writerow(["field", "value"])
        w.writerow(["name", patient.name or ""])
        w.writerow(["age", patient.age if patient.age is not None else ""])
        w.writerow(["sex", patient.sex or ""])
        w.writerow(["conditions", patient.conditions or ""])
        w.writerow(["medical_history", patient.medical_history or ""])
        w.writerow(["diet_notes", patient.diet_notes or ""])
        w.writerow(["hydration_habits", patient.hydration_habits or ""])
        w.writerow(["smoking", patient.smoking or ""])
        w.writerow(["export_date_utc", export_date])
        zf.writestr("patient_info.csv", bio.getvalue())

        # vitals.csv
        bio = io.StringIO()
        w = csv.writer(bio)
        w.writerow(["logged_at_utc", "systolic_bp_mmHg", "diastolic_bp_mmHg", "heart_rate_bpm", "weight_kg", "temperature_c", "triage_flag", "triage_note"])
        for v in vitals:
            logged = v.logged_at.isoformat() if hasattr(v.logged_at, "isoformat") else str(v.logged_at)
            w.writerow([
                logged,
                v.systolic_bp if v.systolic_bp is not None else "",
                v.diastolic_bp if v.diastolic_bp is not None else "",
                v.heart_rate if v.heart_rate is not None else "",
                v.weight_kg if v.weight_kg is not None else "",
                v.temperature_c if v.temperature_c is not None else "",
                v.triage_flag or "",
                (v.triage_note or "").replace("\n", " "),
            ])
        zf.writestr("vitals.csv", bio.getvalue())

        # medication_logs.csv
        bio = io.StringIO()
        w = csv.writer(bio)
        w.writerow(["taken_at_utc", "medication_name", "dosage", "frequency", "status", "note"])
        for log in med_logs:
            taken = log.taken_at.isoformat() if hasattr(log.taken_at, "isoformat") else str(log.taken_at)
            info = med_id_to_info.get(log.medication_id, {"name": "Unknown", "dosage": "", "frequency": ""})
            status = "skipped" if log.skipped else "taken"
            w.writerow([taken, info["name"], info["dosage"], info["frequency"], status, (log.note or "").replace("\n", " ")])
        zf.writestr("medication_logs.csv", bio.getvalue())

        # symptoms.csv
        bio = io.StringIO()
        w = csv.writer(bio)
        w.writerow(["logged_at_utc", "symptoms", "severity", "notes"])
        for s in symptoms:
            logged = s.logged_at.isoformat() if hasattr(s.logged_at, "isoformat") else str(s.logged_at)
            w.writerow([logged, (s.symptoms or "").replace("\n", " "), s.severity or "", (s.notes or "").replace("\n", " ")])
        zf.writestr("symptoms.csv", bio.getvalue())

    buf.seek(0)
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
    )


@router.get("/{patient_id}/risk-score")
async def get_patient_risk_score(patient_id: int, db: AsyncSession = Depends(get_db)):
    """HF risk score (0–100) and tier from UCI Heart Failure Clinical Records model + patient vitals/symptoms."""
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    vitals_r = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.patient_id == patient_id)
        .order_by(desc(VitalsLog.logged_at))
        .limit(14)
    )
    vitals = list(vitals_r.scalars().all())
    if not vitals:
        # No vitals entered yet: don't show a numeric risk score.
        result = compute_risk(
            age=getattr(patient, "age", None),
            sex=getattr(patient, "sex", None),
            vitals_sbp=None,
            vitals_dbp=None,
            vitals_hr=None,
            vitals_weight=None,
            symptom_count_7d=0,
        )
        return {
            "score": None,
            "tier": "unavailable",
            "dataset_name": result.dataset_name,
            "disclaimer": result.disclaimer,
        }
    since_7d = (datetime.now(timezone.utc) - timedelta(days=7)).replace(tzinfo=None)
    symptoms_r = await db.execute(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient_id, SymptomLog.logged_at >= since_7d)
    )
    symptom_count_7d = len(list(symptoms_r.scalars().all()))
    sbp = [v.systolic_bp for v in vitals if v.systolic_bp is not None]
    dbp = [v.diastolic_bp for v in vitals if v.diastolic_bp is not None]
    hr = [v.heart_rate for v in vitals if v.heart_rate is not None]
    weight = [v.weight_kg for v in vitals if v.weight_kg is not None]
    age = getattr(patient, "age", None)
    sex = getattr(patient, "sex", None)
    result = compute_risk(
        age=age,
        sex=sex,
        vitals_sbp=sbp or None,
        vitals_dbp=dbp or None,
        vitals_hr=hr or None,
        vitals_weight=weight or None,
        symptom_count_7d=symptom_count_7d,
    )
    # Apply vitals-based adjustment: UCI model has no HR/BP thresholds, so raise score when triage flags critical/warning
    score = result.score
    tier = result.tier
    if vitals:
        latest = vitals[0]
        prev_weight = vitals[1].weight_kg if len(vitals) > 1 else None
        triage = triage_vitals(
            systolic_bp=latest.systolic_bp,
            diastolic_bp=latest.diastolic_bp,
            heart_rate=latest.heart_rate,
            weight_kg=latest.weight_kg,
            previous_weight_kg=prev_weight,
            temperature_c=latest.temperature_c,
        )
        if triage.flag == "critical":
            score = min(100, score + 35)
        elif triage.flag == "warning":
            score = min(100, score + 18)
        # Derive tier from score (continuous); vitals override ensures at least moderate/high when abnormal
        if score < 34:
            tier = "low"
        elif score < 67:
            tier = "moderate"
        else:
            tier = "high"
        if triage.flag == "critical" and tier != "high":
            tier = "high"
        elif triage.flag == "warning" and tier == "low":
            tier = "moderate"
    else:
        tier = result.tier
    return {
        "score": score,
        "tier": tier,
        "dataset_name": result.dataset_name,
        "disclaimer": result.disclaimer,
    }


def _build_rule_based_daily_message(
    patient: Patient,
    vitals_history: list[VitalsLog],
    symptom_history: list[SymptomLog],
    med_logs: list[MedicationLog],
    meds: list[Medication],
) -> str:
    """Fallback daily message: personalized from vitals, meds, symptoms, and time of day."""
    name = (patient.name or "").strip()
    salutation = f"{name}," if name else "Today"
    now = datetime.now(timezone.utc)
    today = now.date()
    time_desc = "morning" if 5 <= now.hour < 12 else "afternoon" if 12 <= now.hour < 17 else "evening"

    latest_vital = vitals_history[0] if vitals_history else None
    prev_weight = vitals_history[1].weight_kg if len(vitals_history) > 1 else None

    triage = None
    if latest_vital:
        triage = triage_vitals(
            systolic_bp=latest_vital.systolic_bp,
            diastolic_bp=latest_vital.diastolic_bp,
            heart_rate=latest_vital.heart_rate,
            weight_kg=latest_vital.weight_kg,
            previous_weight_kg=prev_weight,
            temperature_c=latest_vital.temperature_c,
        )

    skipped_today = [
        log for log in med_logs if log.taken_at and log.taken_at.date() == today and log.skipped
    ]
    taken_today = [
        log for log in med_logs if log.taken_at and log.taken_at.date() == today and not log.skipped
    ]
    med_id_to_name = {m.id: m.name for m in meds}

    # Only list vitals that are abnormal (recommendation highlights what needs attention, not normal readings)
    vital_parts = []
    bp_abnormal = False
    hr_abnormal = False
    temp_abnormal = False
    weight_gain_abnormal = False
    if latest_vital and (triage and triage.flag):
        s = get_settings()
        sbp, dbp = latest_vital.systolic_bp, latest_vital.diastolic_bp
        sbp_abnormal = sbp is not None and (
            sbp >= s.vitals_sbp_high or sbp <= s.vitals_sbp_low or sbp >= 160 or sbp <= 100
        )
        dbp_abnormal = dbp is not None and (dbp >= s.vitals_dbp_high or dbp <= s.vitals_dbp_low)
        bp_abnormal = sbp_abnormal or dbp_abnormal
        if bp_abnormal:
            vital_parts.append(f"BP {sbp or '?'}/{dbp or '?'}")

        hr = latest_vital.heart_rate
        hr_abnormal = hr is not None and (hr >= s.vitals_hr_high or hr <= s.vitals_hr_low)
        if hr_abnormal:
            vital_parts.append(f"heart rate {hr} bpm")

        if latest_vital.weight_kg is not None and prev_weight is not None:
            gain = latest_vital.weight_kg - prev_weight
            weight_gain_abnormal = gain >= s.vitals_weight_gain_kg_alert
            if weight_gain_abnormal:
                vital_parts.append(f"weight gain {gain:.1f} kg")

        temp = latest_vital.temperature_c
        temp_abnormal = temp is not None and (temp >= s.vitals_temp_high or temp <= s.vitals_temp_low)
        if temp_abnormal:
            vital_parts.append(f"temperature {temp:.1f}°C")
    vital_str = ", ".join(vital_parts) if vital_parts else ""

    if triage and triage.flag == "critical":
        specific = f" ({vital_str})" if vital_str else ""
        # If the only critical issue is rapid weight gain, don't instruct to recheck full vitals now.
        if weight_gain_abnormal and not (bp_abnormal or hr_abnormal or temp_abnormal):
            return (
                f"{salutation} your latest reading{specific} needs attention—confirm your scale reading and recheck your weight tomorrow morning. "
                "Watch for swelling or shortness of breath, and contact your care team if symptoms worsen."
            )
        return (
            f"{salutation} your latest readings{specific} need attention—recheck your vitals now and contact your care "
            "team or emergency services if you feel worse."
        )

    if triage and triage.flag == "warning":
        specific = f" Given your latest ({vital_str})," if vital_str else ""
        return (
            f"{salutation}{specific} slow down today: limit salt and fluids, log your weight, and contact your care team if symptoms get worse."
        )

    if skipped_today and meds:
        skipped_names = [med_id_to_name.get(log.medication_id) or "a medication" for log in skipped_today]
        med_ref = skipped_names[0] if len(skipped_names) == 1 else "at least one heart medicine"
        return (
            f"{salutation} you skipped {med_ref} today—log what you actually took and try to get back on schedule."
        )

    if taken_today and meds:
        med_ref = ", ".join(m.name for m in meds[:2]) if meds else "your heart medicines"
        if len(meds) > 2:
            med_ref += " and others"
        return (
            f"{salutation} you're on track with {med_ref}. Keep it up and log your weight and any symptoms today."
        )

    if latest_vital and latest_vital.weight_kg is not None:
        return (
            f"{salutation} keep your weight steady ({latest_vital.weight_kg} kg): avoid extra salt, follow your fluid limit, and log again tomorrow {time_desc}."
        )

    if symptom_history:
        recent = symptom_history[0]
        sym_ref = (recent.symptoms or "symptoms")[:60]
        return (
            f"{salutation} you recently noted {sym_ref}. Watch for changes today, rest as needed, and contact your care team if you feel worse."
        )

    if meds:
        def _matches_time_window(time_of_day: str | None) -> bool:
            if not time_of_day:
                return False
            s = str(time_of_day).lower()
            if time_desc == "morning":
                return any(k in s for k in ["morning", "breakfast", "after breakfast", "before breakfast", "am", "a.m"])
            if time_desc == "afternoon":
                return any(k in s for k in ["afternoon", "lunch", "noon", "midday", "pm", "p.m"])
            # evening
            return any(k in s for k in ["evening", "dinner", "supper", "bed", "bedtime", "night"])

        due = [m.name for m in meds if _matches_time_window(getattr(m, "time_of_day", None))]
        pick = due if due else [m.name for m in meds]
        pick = [p for p in pick if p]
        if not pick:
            med_ref = "your heart medicines"
        else:
            shown = pick[:2]
            med_ref = " and ".join(shown) if len(shown) <= 2 else ", ".join(shown)
            if len(pick) > 2:
                med_ref += " and others"
        return (
            f"{salutation} take {med_ref} on time this {time_desc}, and log your weight and any new symptoms."
        )

    return (
        f"{salutation} this {time_desc}, focus on one habit: limit salt, take a short walk if you can, and drink fluids as your care team advised."
    )


@router.get("/{patient_id}/daily-message")
async def get_patient_daily_message(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Return a short, personalized daily message (time-aware, actionable) for the dashboard."""
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    meds_r = await db.execute(
        select(Medication).where(Medication.patient_id == patient_id, Medication.active == True)
    )
    meds = list(meds_r.scalars().all())
    med_id_to_name = {m.id: m.name for m in meds}
    vitals_r = await db.execute(
        select(VitalsLog)
        .where(VitalsLog.patient_id == patient_id)
        .order_by(desc(VitalsLog.logged_at))
        .limit(14)
    )
    vitals_history = list(vitals_r.scalars().all())
    symptoms_r = await db.execute(
        select(SymptomLog)
        .where(SymptomLog.patient_id == patient_id)
        .order_by(desc(SymptomLog.logged_at))
        .limit(10)
    )
    symptom_history = list(symptoms_r.scalars().all())
    med_logs_r = await db.execute(
        select(MedicationLog)
        .where(MedicationLog.patient_id == patient_id)
        .order_by(desc(MedicationLog.taken_at))
        .limit(30)
    )
    med_logs = list(med_logs_r.scalars().all())
    chat_r = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.patient_id == patient_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(20)
    )
    chat_history_reversed = list(chat_r.scalars().all())
    chat_history = list(reversed(chat_history_reversed))
    context = format_patient_context(
        patient, meds, vitals_history, symptom_history, med_logs, med_id_to_name, chat_history
    )

    # Add an explicit "latest entry" summary so the LLM always prioritizes the newest logs.
    latest = vitals_history[0] if vitals_history else None
    prev_weight = vitals_history[1].weight_kg if len(vitals_history) > 1 else None
    triage = None
    weight_gain = None
    if latest:
        triage = triage_vitals(
            systolic_bp=latest.systolic_bp,
            diastolic_bp=latest.diastolic_bp,
            heart_rate=latest.heart_rate,
            weight_kg=latest.weight_kg,
            previous_weight_kg=prev_weight,
            temperature_c=latest.temperature_c,
        )
        if latest.weight_kg is not None and prev_weight is not None:
            weight_gain = latest.weight_kg - prev_weight

    latest_lines = ["=== LATEST VITALS / CURRENT STATUS (PRIORITIZE THIS) ==="]
    if latest:
        bp = f"{latest.systolic_bp}/{latest.diastolic_bp}" if latest.systolic_bp is not None else "—"
        hr = str(latest.heart_rate) if latest.heart_rate is not None else "—"
        wt = f"{latest.weight_kg} kg" if latest.weight_kg is not None else "—"
        latest_lines.append(f"Latest BP: {bp}")
        latest_lines.append(f"Latest HR: {hr}")
        latest_lines.append(f"Latest weight: {wt}")
        if weight_gain is not None:
            latest_lines.append(f"Weight change vs prior entry: {weight_gain:+.1f} kg")
        if triage:
            latest_lines.append(f"Triage flag: {triage.flag or 'none'}")
            latest_lines.append(f"Triage note: {triage.note}")
    else:
        latest_lines.append("No vitals logged yet.")

    context = "\n".join(latest_lines) + "\n\n" + context

    # Try LLM-based message first; if unavailable, use rule-based fallback.
    message = await get_daily_message(context)
    if not message:
        message = _build_rule_based_daily_message(
            patient=patient,
            vitals_history=vitals_history,
            symptom_history=symptom_history,
            med_logs=med_logs,
            meds=meds,
        )
    return {"message": message}


@router.patch("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: int, data: PatientUpdate, db: AsyncSession = Depends(get_db)
):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(patient, k, v)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = r.scalar_one_or_none()
    if not patient:
        raise HTTPException(404, "Patient not found")
    await db.delete(patient)
    await db.commit()
