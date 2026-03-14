import { useState, useEffect, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { API } from "../App";
import { renderMessageContent } from "../utils/formatMessage";

export default function Recommendations() {
  const { patientId } = useParams();
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (!patientId) return;
    fetch(`${API}/patients/${patientId}/chat/history`)
      .then((r) => r.json())
      .then((list) => {
        if (Array.isArray(list)) {
          setHistory(list.map((m) => ({ role: m.role, content: m.content })));
          const lastAssistant = list.filter((m) => m.role === "assistant").pop();
          if (lastAssistant) setResponse(lastAssistant.content);
        }
      })
      .catch(() => {});
  }, [patientId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, loading]);

  const send = (e) => {
    e.preventDefault();
    const userMessage = message.trim();
    if (!userMessage) return;
    setLoading(true);
    setHistory((prev) => [...prev, { role: "user", content: userMessage }]);
    setMessage("");
    fetch(`${API}/patients/${patientId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: userMessage,
        recent_summary: response || "",
      }),
    })
      .then(async (r) => {
        const data = await r.json().catch(() => ({}));
        const text = data.response ?? data.detail ?? (Array.isArray(data.detail) ? data.detail[0]?.msg : null) ?? "Something went wrong. Please try again.";
        if (!r.ok) {
          throw new Error(typeof text === "string" ? text : "Something went wrong.");
        }
        return { response: typeof data.response === "string" ? data.response : text };
      })
      .then((data) => {
        const resp = data.response || "";
        setResponse(resp);
        setHistory((prev) => [...prev, { role: "assistant", content: resp }]);
      })
      .catch((err) => {
        const message = err.message || "Sorry, something went wrong. Please try again.";
        setResponse(message);
        setHistory((prev) => [...prev, { role: "assistant", content: message }]);
      })
      .finally(() => setLoading(false));
  };

  return (
    <>
      <h2>Chat history</h2>
      <p className="muted">
        Ask about diet, fluids, exercise, medications, or symptoms. DailyCare uses heart failure guidelines to give safe, supportive advice.
      </p>

      <div className="card">
        <h3>Chat with DailyCare</h3>
        <div
          className="chat-history-scroll"
          style={{
            maxHeight: "380px",
            overflowY: "auto",
            marginBottom: "1rem",
            paddingRight: "0.25rem",
          }}
        >
          {history.length === 0 && !loading && (
            <p className="muted">Try: “What should I eat with heart failure?” or “Can I have salt?” or “When should I call the doctor?”</p>
          )}
          {history.map((h, i) => (
            <div
              key={i}
              style={{
                marginBottom: "0.75rem",
                padding: "0.75rem",
                borderRadius: "8px",
                background: h.role === "user" ? "var(--bg)" : "var(--surface)",
                border: "1px solid var(--border)",
              }}
            >
              <strong>{h.role === "user" ? "You" : "DailyCare"}</strong>
              <p style={{ margin: "0.25rem 0 0", whiteSpace: "pre-wrap" }}>
                {h.role === "assistant" ? renderMessageContent(h.content) : h.content}
              </p>
            </div>
          ))}
          {loading && <p className="muted">DailyCare is thinking…</p>}
          <div ref={chatEndRef} />
        </div>
        <form onSubmit={send}>
          <label className="label" htmlFor="msg">Your question</label>
          <textarea
            id="msg"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="e.g. What fluids can I have?"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !message.trim()} style={{ marginTop: "0.5rem" }}>
            {loading ? "Sending…" : "Send"}
          </button>
        </form>
      </div>

      <p><Link to={`/patient/${patientId}`}>← Back to home</Link></p>
    </>
  );
}
