import { useState } from "react";
import styles from "../styles/ChatPanel.module.css";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  messages: ChatMessage[];
  loading: boolean;
  error: string;
  onSend: (message: string) => Promise<void>;
  suggestions?: string[];
};

export function ChatPanel({ messages, loading, error, onSend, suggestions = [] }: Props) {
  const [input, setInput] = useState("");
  const hasMessages = messages.length > 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    await onSend(text);
  }

  function assistantTag(content: string) {
    const lc = content.toLowerCase();
    if (lc.includes("outside the scope")) return "Scope";
    if (lc.includes("monitor") || lc.includes("next") || lc.includes("recommend")) return "Action";
    return "Insight";
  }

  function normalizeLine(line: string) {
    return line.replace(/^[-*•]\s+/, "").replace(/\*\*/g, "").trim();
  }

  function clip(text: string, max = 120) {
    if (text.length <= max) return text;
    return `${text.slice(0, max - 1).trimEnd()}…`;
  }

  function toStructuredAssistantContent(content: string) {
    const lines = content.split("\n").map((line) => line.trim()).filter(Boolean);
    const cleanedLines = lines.map(normalizeLine).filter(Boolean);
    const bullets = lines.filter((line) => /^[-*•]\s+/.test(line)).map(normalizeLine);
    const source = bullets.length ? bullets : cleanedLines;

    const metricPattern =
      /\b(hr|heart rate|eda|temp|temperature|movement|stress|high stress|readings?)\b[^0-9-]*(-?\d+(\.\d+)?%?)/i;

    const metrics = source
      .map((line) => {
        const match = line.match(metricPattern);
        if (!match) return null;
        return {
          label: match[1].replace(/\b\w/g, (c) => c.toUpperCase()),
          value: match[2],
        };
      })
      .filter((item): item is { label: string; value: string } => Boolean(item))
      .slice(0, 3);

    const actionText = clip(
      source.find((line) => /recommend|action|monitor|attention|prioritize/i.test(line)) || source[0] || "",
      126,
    );

    const insightCards = source
      .filter((line) => normalizeLine(line) !== normalizeLine(actionText))
      .slice(0, 4)
      .map((line) => {
        const [title, ...rest] = line.split(/[:\-]\s+/);
        if (!rest.length) {
          return { title: "Insight", body: clip(line, 120) };
        }
        return { title: clip(title || "Insight", 40), body: clip(rest.join(" - "), 120) };
      });

    const compactInsightCards = insightCards.slice(0, 4);
    const isCompact =
      metrics.length === 0 &&
      compactInsightCards.length <= 2 &&
      compactInsightCards.every((item) => item.body.length <= 95);

    return { actionText, metrics, insightCards: compactInsightCards, isCompact };
  }

  function renderMessageBody(message: ChatMessage) {
    if (message.role === "assistant") {
      const structured = toStructuredAssistantContent(message.content);
      if (structured.isCompact) {
        return (
          <div className={styles.assistantStack}>
            <div className={styles.assistantMeta}>
              <div className={styles.assistantAvatar}>CS</div>
              <span>{assistantTag(message.content)} brief</span>
            </div>
            <article className={styles.compactCard}>
              {structured.insightCards.map((item, idx) => (
                <p key={`${item.title}-${idx}`}>
                  <strong>{item.title}:</strong> {item.body}
                </p>
              ))}
            </article>
            <p className={styles.footerNote}>Context-aware output from current dashboard state</p>
          </div>
        );
      }
      return (
        <div className={styles.assistantStack}>
          <div className={styles.assistantMeta}>
            <div className={styles.assistantAvatar}>CS</div>
            <span>{assistantTag(message.content)} brief</span>
          </div>

          {structured.actionText ? (
            <div className={styles.banner}>
              <span className={styles.bannerTag}>Action recommended</span>
              <p>{structured.actionText}</p>
            </div>
          ) : null}

          {structured.metrics.length ? (
            <div className={styles.metricGrid}>
              {structured.metrics.map((metric, idx) => (
                <div key={`${metric.label}-${idx}`} className={styles.metricCard}>
                  <span>{metric.label}</span>
                  <strong>{metric.value}</strong>
                </div>
              ))}
            </div>
          ) : null}

          <div className={styles.insightGrid}>
            {structured.insightCards.length ? (
              structured.insightCards.map((item, idx) => (
                <article key={`${item.title}-${idx}`} className={styles.insightCard}>
                  <h5>{item.title}</h5>
                  <p>{item.body}</p>
                </article>
              ))
            ) : (
              <article className={styles.insightCard}>
                <h5>Insight</h5>
                <p className={styles.assistantText}>{message.content}</p>
              </article>
            )}
          </div>

          <p className={styles.footerNote}>Context-aware output from current dashboard state</p>
        </div>
      );
    }
    return <p className={styles.userText}>{message.content}</p>;
  }

  return (
    <section className={styles.panel}>
      <div className={styles.messages}>
        {!hasMessages && (
          <div className={styles.emptyState}>
            <p className={styles.placeholderTitle}>Ask your analytics assistant</p>
            <p className={styles.placeholder}>
              Start with one question about this month, caregiver patterns, or unusual stress signals.
            </p>
          </div>
        )}
        {messages.map((message, idx) => (
          <article
            key={`${message.role}-${idx}`}
            className={`${styles.message} ${message.role === "user" ? styles.user : styles.assistant}`}
          >
            {renderMessageBody(message)}
          </article>
        ))}
        {loading ? (
          <article className={`${styles.message} ${styles.assistant} ${styles.typingMessage}`}>
            <div className={styles.typingWrap}>
              <div className={styles.assistantAvatar}>CS</div>
              <div className={styles.typingBubble} aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </article>
        ) : null}
      </div>
      {suggestions.length ? (
        <div className={styles.suggestions}>
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => onSend(suggestion)}
              disabled={loading}
            >
              {suggestion}
            </button>
          ))}
        </div>
      ) : null}
      {error ? <p className={styles.error}>{error}</p> : null}
      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about stress patterns, caregivers, or trends..."
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </form>
    </section>
  );
}
