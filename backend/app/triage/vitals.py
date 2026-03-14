"""
Triage engine for vitals. Flags severe/abnormal values in heart failure context.
"""
from dataclasses import dataclass
from typing import Optional
from app.config import get_settings


@dataclass
class TriageResult:
    flag: str  # "" | "warning" | "critical"
    note: str
    should_escalate: bool


def triage_vitals(
    *,
    systolic_bp: Optional[int] = None,
    diastolic_bp: Optional[int] = None,
    heart_rate: Optional[int] = None,
    weight_kg: Optional[float] = None,
    previous_weight_kg: Optional[float] = None,
    temperature_c: Optional[float] = None,
) -> TriageResult:
    settings = get_settings()
    notes: list[str] = []
    max_severity = ""

    if systolic_bp is not None:
        if systolic_bp >= settings.vitals_sbp_high:
            notes.append(f"High systolic BP ({systolic_bp} mmHg). Consider contacting care team.")
            max_severity = "critical" if max_severity != "critical" else "critical"
        elif systolic_bp <= settings.vitals_sbp_low:
            notes.append(f"Low systolic BP ({systolic_bp} mmHg). May indicate dizziness or worsening HF.")
            max_severity = "critical" if max_severity != "critical" else "critical"
        elif systolic_bp >= 160 or systolic_bp <= 100:
            notes.append(f"Systolic BP ({systolic_bp} mmHg) outside ideal range. Monitor.")
            if max_severity != "critical":
                max_severity = "warning"

    if diastolic_bp is not None:
        if diastolic_bp >= settings.vitals_dbp_high or diastolic_bp <= settings.vitals_dbp_low:
            notes.append(f"Diastolic BP ({diastolic_bp} mmHg) outside safe range.")
            if max_severity != "critical":
                max_severity = "warning"

    if heart_rate is not None:
        if heart_rate >= settings.vitals_hr_high:
            notes.append(f"High heart rate ({heart_rate} bpm). Rest and recheck; contact if persistent.")
            max_severity = "critical" if max_severity != "critical" else "critical"
        elif heart_rate <= settings.vitals_hr_low:
            notes.append(f"Low heart rate ({heart_rate} bpm). Report to care team if symptomatic.")
            if max_severity != "critical":
                max_severity = "warning"

    if weight_kg is not None and previous_weight_kg is not None:
        gain = weight_kg - previous_weight_kg
        if gain >= settings.vitals_weight_gain_kg_alert:
            notes.append(
                f"Weight gain of {gain:.1f} kg in short time. Possible fluid retention—contact care team."
            )
            max_severity = "critical" if max_severity != "critical" else "critical"

    if temperature_c is not None:
        if temperature_c >= settings.vitals_temp_high:
            notes.append(f"Fever ({temperature_c:.1f}°C). May indicate infection. Contact care team.")
            max_severity = "critical" if max_severity != "critical" else "critical"
        elif temperature_c <= settings.vitals_temp_low:
            notes.append(f"Low temperature ({temperature_c:.1f}°C). Keep warm; report if unwell.")
            if max_severity != "critical":
                max_severity = "warning"

    note_str = " ".join(notes) if notes else "Vitals within acceptable range."
    should_escalate = max_severity == "critical"
    return TriageResult(flag=max_severity, note=note_str, should_escalate=should_escalate)
