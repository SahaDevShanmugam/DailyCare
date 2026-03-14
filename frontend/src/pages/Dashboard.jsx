import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";
import { renderMessageContent } from "../utils/formatMessage";

const MED_COLORS = ["blue", "purple", "teal"];

const MicIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
    <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
    <line x1="12" y1="19" x2="12" y2="22" />
    <line x1="8" y1="22" x2="16" y2="22" />
  </svg>
);

/** Mic icon with a volume-level fill inside the mic head (0–100). */
function MicWithLevel({ level = 0, listening = false }) {
  const fillHeight = Math.max(0, Math.min(100, level)) / 100 * 7;
  const color = listening ? "var(--danger)" : "var(--primary)";
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>
      <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
      {level > 5 && (
        <rect x="10" y={13 - fillHeight} width="4" height={fillHeight} rx="1" fill={color} opacity="0.85" />
      )}
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
    </svg>
  );
}

function getSpeechRecognition() {
  if (typeof window === "undefined") return null;
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function speakText(text, onEnd) {
  if (typeof window === "undefined" || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = 0.9;
  u.pitch = 1;
  const voices = window.speechSynthesis.getVoices();
  const en = voices.find((v) => v.lang.startsWith("en"));
  if (en) u.voice = en;
  u.onend = () => {
    if (onEnd) onEnd();
  };
  u.onerror = () => {
    if (onEnd) onEnd();
  };
  window.speechSynthesis.speak(u);
}

export default function Dashboard() {
  const { patientId } = useParams();
  const [patient, setPatient] = useState(null);
  const [meds, setMeds] = useState([]);
  const [lastVitals, setLastVitals] = useState(null);
  const [riskEvents, setRiskEvents] = useState([]);
  const [confirmingMedId, setConfirmingMedId] = useState(null);
  const [assistantMessage, setAssistantMessage] = useState("");
  const [assistantInput, setAssistantInput] = useState("");
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [voiceListening, setVoiceListening] = useState(false);
  const [voiceError, setVoiceError] = useState(null);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [lastVoiceTranscript, setLastVoiceTranscript] = useState("");
  const [micLevel, setMicLevel] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  const analyserRef = useRef(null);
  const animationRef = useRef(null);
  const [readResponseAloud, setReadResponseAloud] = useState(true);
  const [dailyMessage, setDailyMessage] = useState("");
  const [dailyMessageLoading, setDailyMessageLoading] = useState(false);
  const [medLogs, setMedLogs] = useState([]);
  const [confirmedMedIds, setConfirmedMedIds] = useState(new Set());
  const [justConfirmedId, setJustConfirmedId] = useState(null);
  const [riskScore, setRiskScore] = useState(null);
  const [riskScoreLoading, setRiskScoreLoading] = useState(false);

  const loadData = () => {
    if (!patientId) return;
    const noCache = { cache: "no-store" };
    Promise.all([
      fetch(`${API}/patients/${patientId}`, noCache).then((r) => r.json()),
      fetch(`${API}/patients/${patientId}/medications`, noCache).then((r) => r.json()),
      fetch(`${API}/patients/${patientId}/vitals?limit=1`, noCache).then((r) => r.json()),
      fetch(`${API}/patients/${patientId}/risk-events?acknowledged=false&limit=5`, noCache).then((r) => r.json()),
      fetch(`${API}/patients/${patientId}/medications/log?limit=50`, noCache).then((r) => r.json()),
    ])
      .then(([p, m, v, r, logs]) => {
        setPatient(p);
        setMeds(m);
        setLastVitals(Array.isArray(v) && v[0] ? v[0] : null);
        setRiskEvents(Array.isArray(r) ? r : []);
        setMedLogs(Array.isArray(logs) ? logs : []);
      })
      .catch(() => setPatient(null));
  };

  useEffect(loadData, [patientId]);

  useEffect(() => {
    if (!patientId) return;
    setDailyMessageLoading(true);
    fetch(`${API}/patients/${patientId}/daily-message`)
      .then((r) => r.json())
      .then((data) => setDailyMessage(data.message || ""))
      .catch(() => setDailyMessage(""))
      .finally(() => setDailyMessageLoading(false));
  }, [patientId]);

  useEffect(() => {
    if (!patientId) return;
    setRiskScoreLoading(true);
    fetch(`${API}/patients/${patientId}/risk-score`, { cache: "no-store" })
      .then((r) => r.json())
      .then((data) => setRiskScore(data))
      .catch(() => setRiskScore(null))
      .finally(() => setRiskScoreLoading(false));
  }, [patientId]);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort?.();
          recognitionRef.current.stop?.();
        } catch (_) {}
        recognitionRef.current = null;
      }
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      streamRef.current?.getTracks?.().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  const confirmTaken = (medicationId) => {
    setConfirmingMedId(medicationId);
    fetch(`${API}/patients/${patientId}/medications/log`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ medication_id: medicationId, skipped: false, note: "" }),
    })
      .then((r) => {
        if (r.ok) {
          setJustConfirmedId(medicationId);
          setTimeout(() => setJustConfirmedId(null), 1500);
          setConfirmedMedIds((prev) => new Set([...prev, medicationId]));
          // Refetch logs so when user navigates away and back, taken state comes from server
          fetch(`${API}/patients/${patientId}/medications/log?limit=50`, { cache: "no-store" })
            .then((res) => res.json())
            .then((logs) => setMedLogs(Array.isArray(logs) ? logs : []))
            .catch(() => {});
        }
      })
      .finally(() => setConfirmingMedId(null));
  };

  const now = new Date();
  const currentMinutes = now.getHours() * 60 + now.getMinutes();
  const isSameCalendarDay = (dateStr) => {
    if (!dateStr) return false;
    const s = String(dateStr).trim().replace(" ", "T");
    const asUtc = /Z|[+-]\d{2}:?\d{2}$/.test(s) ? s : s.replace(/\.\d+$/, "") + "Z";
    const d = new Date(asUtc);
    if (Number.isNaN(d.getTime())) return false;
    return (
      d.getFullYear() === now.getFullYear() &&
      d.getMonth() === now.getMonth() &&
      d.getDate() === now.getDate()
    );
  };
  const takenTodayMedIds = new Set(
    medLogs
      .filter(
        (log) =>
          log.medication_id != null &&
          !log.skipped &&
          isSameCalendarDay(log.taken_at)
      )
      .map((log) => Number(log.medication_id))
  );
  const isTaken = (medId) =>
    takenTodayMedIds.has(Number(medId)) || confirmedMedIds.has(medId);

  const getTimeWindowForMedication = (label) => {
    if (!label) return null;
    const s = String(label).toLowerCase().trim();
    const timeMatch = s.match(/(\d{1,2}):(\d{2})/);
    if (timeMatch) {
      const hour = parseInt(timeMatch[1], 10);
      const minute = parseInt(timeMatch[2], 10);
      if (Number.isNaN(hour) || Number.isNaN(minute) || hour > 23 || minute > 59) {
        return null;
      }
      const center = hour * 60 + minute;
      const start = Math.max(0, center - 45);
      const end = Math.min(24 * 60, center + 45);
      return [start, end];
    }
    if (s.includes("morning") || s.includes("breakfast")) return [6 * 60, 11 * 60];
    if (s.includes("noon") || s.includes("lunch")) return [11 * 60, 14 * 60];
    if (s.includes("afternoon")) return [12 * 60, 17 * 60];
    if (s.includes("evening")) return [17 * 60, 21 * 60];
    if (s.includes("night") || s.includes("bed") || s.includes("bedtime") || s.includes("dinner") || s.includes("supper")) {
      return [18 * 60, 23 * 60 + 59];
    }
    return null;
  };

  const dueMeds = meds.filter((m) => {
    if (!m || !m.time_of_day) return false;
    if (isTaken(m.id)) return false;
    const window = getTimeWindowForMedication(m.time_of_day);
    if (!window) return false;
    const [start, end] = window;
    return currentMinutes >= start && currentMinutes <= end;
  });

  const stopReadingAloud = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  };

  const sendToAssistant = (e) => {
    e.preventDefault();
    const msg = assistantInput.trim();
    if (!msg) return;
    stopReadingAloud();
    setLastVoiceTranscript("");
    setAssistantLoading(true);
    fetch(`${API}/patients/${patientId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, recent_summary: assistantMessage || "" }),
    })
      .then(async (r) => {
        const data = await r.json().catch(() => ({}));
        const text = data.response ?? data.detail ?? "Something went wrong. Please try again.";
        if (!r.ok) throw new Error(typeof text === "string" ? text : "Something went wrong.");
        return typeof data.response === "string" ? data.response : text;
      })
      .then((response) => setAssistantMessage(response))
      .catch((err) => setAssistantMessage(err.message || "Sorry, something went wrong. Please try again."))
      .finally(() => setAssistantLoading(false));
    setAssistantInput("");
  };

  const sendVoiceToAgent = (transcript) => {
    if (!transcript || !transcript.trim()) return;
    stopReadingAloud();
    setAssistantLoading(true);
    setVoiceError(null);
    fetch(`${API}/patients/${patientId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: transcript.trim(), recent_summary: assistantMessage || "" }),
    })
      .then(async (r) => {
        const data = await r.json().catch(() => ({}));
        const text = data.response ?? data.detail ?? "Something went wrong. Please try again.";
        if (!r.ok) throw new Error(typeof text === "string" ? text : "Something went wrong.");
        return typeof data.response === "string" ? data.response : text;
      })
      .then((response) => {
        setAssistantMessage(response);
        if (readResponseAloud) {
          setIsSpeaking(true);
          speakText(response, () => setIsSpeaking(false));
        }
      })
      .catch((err) => {
        setAssistantMessage(err.message || "Sorry, something went wrong. Please try again.");
        setVoiceError(err.message);
      })
      .finally(() => setAssistantLoading(false));
  };

  const startVoiceChat = () => {
    const SpeechRecognition = getSpeechRecognition();
    if (!SpeechRecognition) {
      setVoiceError("Voice input is not supported in this browser. Try Chrome or Edge.");
      return;
    }
    setVoiceError(null);
    setLiveTranscript("");
    setLastVoiceTranscript("");
    if (recognitionRef.current && voiceListening) {
      try {
        recognitionRef.current.stop();
      } catch (_) {}
      setVoiceListening(false);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      streamRef.current?.getTracks?.().forEach((t) => t.stop());
      streamRef.current = null;
      setMicLevel(0);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = navigator.language || "en-US";
    recognition.onresult = (e) => {
      const result = e.results[e.results.length - 1];
      const transcript = result[0]?.transcript ?? "";
      const isFinal = result.isFinal;
      if (isFinal) {
        if (transcript.trim()) {
          setLastVoiceTranscript(transcript);
          sendVoiceToAgent(transcript);
        }
        setLiveTranscript("");
      } else {
        setLiveTranscript(transcript);
      }
    };
    recognition.onend = () => {
      setVoiceListening(false);
      setLiveTranscript("");
      setMicLevel(0);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      streamRef.current?.getTracks?.().forEach((t) => t.stop());
      streamRef.current = null;
    };
    recognition.onerror = (e) => {
      setVoiceListening(false);
      setLiveTranscript("");
      setMicLevel(0);
      if (e.error === "not-allowed") setVoiceError("Microphone access was denied.");
      else if (e.error === "no-speech") setVoiceError("No speech heard. Try again.");
      else setVoiceError("Voice error. Try again.");
    };
    recognitionRef.current = recognition;
    try {
      recognition.start();
      setVoiceListening(true);
      navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        streamRef.current = stream;
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioContext();
        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        source.connect(analyser);
        analyserRef.current = analyser;
        const data = new Uint8Array(analyser.frequencyBinCount);
        const tick = () => {
          if (!analyserRef.current || !streamRef.current) return;
          analyser.getByteFrequencyData(data);
          let sum = 0;
          for (let i = 0; i < data.length; i++) sum += data[i];
          const avg = Math.min(100, Math.round((sum / data.length) * 1.5));
          setMicLevel(avg);
          animationRef.current = requestAnimationFrame(tick);
        };
        tick();
      }).catch(() => {});
    } catch (err) {
      setVoiceError("Could not start microphone. Check permissions.");
    }
  };

  // Risk levels for BP/HR (match backend triage: green=normal, yellow=warning, red=critical)
  const getBpRisk = () => {
    const sbp = lastVitals?.systolic_bp;
    const dbp = lastVitals?.diastolic_bp;
    if (sbp == null && dbp == null) return "";
    if (sbp != null && (sbp >= 180 || sbp <= 90)) return "critical";
    if (dbp != null && (dbp >= 110 || dbp <= 60)) return "critical";
    if (sbp != null && (sbp >= 160 || sbp <= 100)) return "warning";
    if (dbp != null && (dbp > 100 && dbp < 110 || dbp > 60 && dbp < 70)) return "warning";
    return "normal";
  };
  const getHrRisk = () => {
    const hr = lastVitals?.heart_rate;
    if (hr == null) return "";
    if (hr >= 120 || hr <= 50) return "critical";
    if ((hr >= 100 && hr < 120) || (hr > 50 && hr < 55)) return "warning";
    return "normal";
  };
  const bpRisk = getBpRisk();
  const hrRisk = getHrRisk();

  if (!patient) return <p className="muted">Loading…</p>;

  const statusGood = riskEvents.length === 0 && (!lastVitals || !lastVitals.triage_flag);
  const bp = lastVitals?.systolic_bp != null ? `${lastVitals.systolic_bp}/${lastVitals.diastolic_bp ?? "—"}` : "—";
  const hr = lastVitals?.heart_rate != null ? String(lastVitals.heart_rate) : "—";

  const dueMedNames = dueMeds.map((m) => m?.name).filter(Boolean);

  return (
    <>
      {dueMedNames.length > 0 && (
        <div className="card med-reminder-banner">
          <div className="med-reminder-pill" aria-hidden="true">
            <svg
              width="30"
              height="30"
              viewBox="0 0 24 24"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g transform="rotate(-45 12 12)">
                <rect
                  x="5"
                  y="8"
                  width="14"
                  height="8"
                  rx="4"
                  fill="#FFFFFF"
                  stroke="#EF4444"
                  strokeWidth="2"
                />
                <rect
                  x="5"
                  y="8"
                  width="7"
                  height="8"
                  rx="4"
                  fill="#EF4444"
                />
              </g>
            </svg>
          </div>
          <div className="med-reminder-content">
            <h3>Medication reminder</h3>
            <p className="med-reminder-text">
              Morning medication reminder: it's time to take{" "}
              {dueMedNames.map((name, idx) => {
                const isLast = idx === dueMedNames.length - 1;
                const isFirst = idx === 0;
                return (
                  <span key={name}>
                    {!isFirst && (isLast ? " and " : ", ")}
                    <strong>{name}</strong>
                  </span>
                );
              })}
              .
            </p>
          </div>
          <button
            type="button"
            className="btn btn-small med-reminder-dismiss"
            onClick={() => {}}
          >
            Dismiss
          </button>
        </div>
      )}
      {dueMeds.length > 0 && (
        <div className="card due-meds-card">
          <h3>Time to take your medication</h3>
          <p className="muted" style={{ marginTop: "0.25rem" }}>
            These medicines are scheduled for around now. Confirm once you have taken them.
          </p>
          {dueMeds.map((m, i) => {
            const taken = isTaken(m.id);
            return (
              <div key={m.id} className={taken ? "med-row med-row--taken" : "med-row"}>
                <div className={`med-bar ${MED_COLORS[i % MED_COLORS.length]}`} />
                <div style={{ flex: 1 }}>
                  <strong>{m.name}</strong>
                  <span className="muted" style={{ display: "block", fontSize: "0.95rem" }}>
                    {m.dosage && `${m.dosage}`} {m.frequency && ` · ${m.frequency}`}
                    {m.time_of_day && ` · ${m.time_of_day}`}
                  </span>
                </div>
                {!taken ? (
                  <button
                    type="button"
                    className="btn btn-outline btn-small"
                    onClick={() => confirmTaken(m.id)}
                    disabled={confirmingMedId === m.id}
                    aria-label={`Confirm ${m.name} taken`}
                  >
                    {confirmingMedId === m.id ? "…" : "✓ Confirm taken"}
                  </button>
                ) : justConfirmedId === m.id ? (
                  <span className="success" style={{ fontWeight: 600 }}>✓ Saved!</span>
                ) : null}
              </div>
            );
          })}
        </div>
      )}
      {riskEvents.length > 0 && (
        <div className="card" style={{ borderLeft: "4px solid var(--danger)" }}>
          <h3 className="danger">Alerts</h3>
          <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
            {riskEvents.map((e) => (
              <li key={e.id}>{e.description}</li>
            ))}
          </ul>
          <p className="muted">Please contact your care team if any of these apply.</p>
        </div>
      )}

      {/* HF Risk Score */}
      <div className="card hf-risk-card">
        <h3>Heart Failure Risk Score</h3>
        {riskScoreLoading ? (
          <p className="muted" style={{ margin: 0 }}>Loading risk score…</p>
        ) : riskScore && riskScore.score != null && riskScore.tier && riskScore.tier !== "unavailable" ? (
          <>
            <div className="hf-risk-display">
              <div
                className={`hf-risk-score-circle hf-risk-tier--${riskScore.tier}`}
                aria-label={`Risk score ${riskScore.score} out of 100`}
              >
                {riskScore.score}
              </div>
              <div className="hf-risk-meta">
                <p style={{ margin: 0, fontWeight: 600, textTransform: "capitalize" }}>{riskScore.tier} risk</p>
                <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
                  Based on vitals and symptom history
                </p>
              </div>
            </div>
            <p className="muted" style={{ marginTop: "0.75rem", marginBottom: 0, fontSize: "0.8rem" }}>
              {riskScore.dataset_name}. {riskScore.disclaimer}
            </p>
          </>
        ) : (
          <>
            <div className="hf-risk-display">
              <div className="hf-risk-score-circle hf-risk-tier--unavailable" aria-label="Risk score unavailable">—</div>
              <div className="hf-risk-meta">
                <p style={{ margin: 0, fontWeight: 600 }}>Unavailable</p>
                <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
                  Log vitals to calculate risk
                </p>
              </div>
            </div>
            <p className="muted" style={{ marginTop: "0.75rem", marginBottom: 0, fontSize: "0.8rem" }}>
              Risk score unavailable. Log vitals and run the model trainer (see backend README).
            </p>
          </>
        )}
      </div>

      {/* Health Status */}
      <div className="health-status-card">
        <h3 className={statusGood ? "status-badged" : "status-badged needs-attention"}>
          Health Status: {statusGood ? "Good" : "Needs attention"}
        </h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem", alignItems: "flex-start", marginTop: "0.5rem" }}>
          <div style={{ flex: "1 1 280px", minWidth: 0 }}>
            <div className="daily-message-box">
              {dailyMessageLoading ? (
                <p className="muted" style={{ margin: 0 }}>Loading your daily tip…</p>
              ) : dailyMessage ? (
                <p style={{ margin: 0 }}>{dailyMessage}</p>
              ) : (
                <p className="muted" style={{ margin: 0 }}>Stay on track with your medications and daily weight today.</p>
              )}
            </div>
          </div>
          <div style={{ display: "flex", gap: "1.25rem", flexWrap: "wrap" }}>
            <div style={{ textAlign: "center" }}>
              <div className={`metric-circle${bpRisk ? ` metric-circle--${bpRisk}` : ""}`}>{bp}</div>
              <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.9rem" }}>Blood Pressure</p>
            </div>
            <div style={{ textAlign: "center" }}>
              <div className={`metric-circle${hrRisk ? ` metric-circle--${hrRisk}` : ""}`}>{hr}</div>
              <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.9rem" }}>Heart Rate</p>
            </div>
          </div>
        </div>
        <div className="section-actions">
          <Link to={`/patient/${patientId}/vitals`} className="btn btn-outline" style={{ textDecoration: "none" }}>
            Health Summary
          </Link>
          <Link to={`/patient/${patientId}/vitals/add`} className="btn section-actions-right" style={{ textDecoration: "none" }}>
            + Add vitals
          </Link>
        </div>
      </div>

      {/* Medications at recommended times with checkmark confirm */}
      <div className="card">
        <h3>Medications</h3>
        {meds.length === 0 ? (
          <p className="muted">No medications listed. <Link to={`/patient/${patientId}/medications`}>Add medications</Link>.</p>
        ) : (
          meds
            .sort((a, b) => (a.time_of_day || "").localeCompare(b.time_of_day || ""))
            .map((m, i) => {
              const taken = isTaken(m.id);
              return (
                <div key={m.id} className={taken ? "med-row med-row--taken" : "med-row"}>
                  <div className={`med-bar ${MED_COLORS[i % MED_COLORS.length]}`} />
                  <div style={{ flex: 1 }}>
                    <strong>{m.name}</strong>
                    <span className="muted" style={{ display: "block", fontSize: "0.95rem" }}>
                      {m.dosage && `${m.dosage}`} {m.frequency && ` · ${m.frequency}`}
                      {m.time_of_day && ` · ${m.time_of_day}`}
                    </span>
                  </div>
                  {!taken ? (
                    <button
                      type="button"
                      className="btn btn-outline btn-small"
                      onClick={() => confirmTaken(m.id)}
                      disabled={confirmingMedId === m.id}
                      aria-label={`Confirm ${m.name} taken`}
                    >
                      {confirmingMedId === m.id ? "…" : "✓ Confirm taken"}
                    </button>
                  ) : justConfirmedId === m.id ? (
                    <span className="success" style={{ fontWeight: 600 }}>✓ Saved!</span>
                  ) : null}
                </div>
              );
            })
        )}
        <div className="section-actions">
          <Link to={`/patient/${patientId}/medications/logs`} className="muted" style={{ marginTop: 0 }}>Recent logs</Link>
          <Link to={`/patient/${patientId}/medications`} className="btn section-actions-right" style={{ textDecoration: "none", marginTop: 0 }}>+ Add medications</Link>
        </div>
      </div>

      {/* Talk to Assistant */}
      <div className="talk-to-assistant-card">
        <h3 style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span style={{ color: "var(--primary)" }}><MicIcon /></span> Talk to Assistant
        </h3>
        <form onSubmit={sendToAssistant}>
          <input
            type="text"
            value={assistantInput}
            onChange={(e) => setAssistantInput(e.target.value)}
            placeholder="Ask about diet, medications, or when to call the doctor…"
            disabled={assistantLoading}
            style={{ marginBottom: "0.5rem" }}
          />
          <div className="chat-actions-row">
            <button
              type="submit"
              className="btn btn-send"
              disabled={assistantLoading || !assistantInput.trim()}
            >
              {assistantLoading ? "Sending…" : "Send"}
            </button>
            <button
              type="button"
              className={`btn btn-voice ${voiceListening ? "listening" : ""}`}
              onClick={startVoiceChat}
              disabled={assistantLoading}
              aria-label={voiceListening ? "Stop listening" : "Speak to Assistant"}
            >
              <span
                className={`mic-level-ring ${voiceListening ? "listening" : ""}`}
                style={{
                  boxShadow: voiceListening && micLevel > 5 ? "0 0 16px rgba(33, 64, 216, 0.35)" : undefined,
                }}
              >
                <MicWithLevel level={micLevel} listening={voiceListening} />
              </span>
              {voiceListening ? "Listening… (click to stop)" : "Speak to Assistant"}
            </button>
          </div>
        </form>
        {voiceListening && (
          <div className="voice-transcript-box">
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>Live transcript:</p>
            <p style={{ margin: "0.25rem 0 0", whiteSpace: "pre-wrap" }}>{liveTranscript || "…"}</p>
          </div>
        )}
        {lastVoiceTranscript && (
          <div className="voice-transcript-box voice-transcript-persistent">
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>You said:</p>
            <p style={{ margin: "0.25rem 0 0", whiteSpace: "pre-wrap" }}>{lastVoiceTranscript}</p>
          </div>
        )}
        {assistantLoading && (
          <div className="agent-loading-indicator">
            <span className="agent-loading-dots" aria-hidden="true" />
            <span>DailyCare is thinking…</span>
          </div>
        )}
        {voiceError && (
          <p className="warning" style={{ marginTop: "0.5rem", marginBottom: 0 }}>{voiceError}</p>
        )}
        <div className="option-row">
          <input
            id="read-aloud-checkbox"
            type="checkbox"
            checked={readResponseAloud}
            onChange={(e) => setReadResponseAloud(e.target.checked)}
            aria-label="Read response aloud"
          />
          <label htmlFor="read-aloud-checkbox" style={{ margin: 0, cursor: "pointer" }}>
            Read response aloud
          </label>
        </div>
        {isSpeaking && (
          <p style={{ marginTop: "0.5rem", marginBottom: 0 }}>
            <span className="muted">Assistant is speaking.</span>
            <button type="button" className="btn-stop-reading" onClick={stopReadingAloud}>
              Stop reading
            </button>
          </p>
        )}
        {assistantMessage && (
          <div className="assistant-response-box">
            <strong>DailyCare:</strong>
            <p style={{ margin: "0.25rem 0 0", whiteSpace: "pre-wrap" }}>{renderMessageContent(assistantMessage)}</p>
          </div>
        )}
        <Link to={`/patient/${patientId}/recommendations`} className="muted" style={{ display: "inline-block", marginTop: "0.5rem" }}>Full chat & history →</Link>
      </div>

      {/* Contact your doctor */}
      <div className="card">
        <h3>Contact your doctor</h3>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", flexWrap: "wrap" }}>
          <img
            src="/doctor-headshot.png"
            alt="Doctor"
            className="contact-avatar"
          />
          <div style={{ flex: 1, minWidth: 120 }}>
            <p style={{ margin: 0 }}>Your care team</p>
            <p className="muted" style={{ margin: "0.25rem 0 0" }}>Call when you have symptoms or questions</p>
          </div>
          <a
            href="tel:"
            className="btn"
            style={{
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "0.4rem",
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 3.11 5.18 2 2 0 0 1 5.1 3h3a1 1 0 0 1 1 .75l1 4a1 1 0 0 1-.27.95l-1.6 1.6a16 16 0 0 0 6.9 6.9l1.6-1.6a1 1 0 0 1 .95-.27l4 1a1 1 0 0 1 .72 1.09z" />
            </svg>
            <span>Call</span>
          </a>
        </div>
        <p className="muted" style={{ marginTop: "0.5rem", fontSize: "0.9rem" }}>
          Add your doctor’s number in your phone. In an emergency, use SOS above.
        </p>
      </div>

    </>
  );
}
