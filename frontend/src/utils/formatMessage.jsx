import React from "react";

/**
 * Renders text with **bold** markdown as <strong>.
 * Splits by ** and alternates normal/strong (no dangerouslySetInnerHTML).
 */
export function renderMessageContent(content) {
  if (typeof content !== "string") return content;
  const parts = content.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    const match = part.match(/^\*\*(.*)\*\*$/);
    if (match) return <strong key={i}>{match[1]}</strong>;
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}
