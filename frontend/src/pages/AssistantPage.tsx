import { ChatPanel, type ChatMessage } from "../components/ChatPanel";
import type { SensorRecord } from "../types";
import styles from "../styles/Assistant.module.css";
import type { ChatMessage as ChatSessionMessage } from "../components/ChatPanel";

type Props = {
  messages: ChatMessage[];
  loading: boolean;
  error: string;
  onSend: (message: string) => Promise<void>;
  selectedMonth: string;
  months: string[];
  onMonthChange: (month: string) => void;
  selectedCell: SensorRecord | null;
  sessions: Array<{
    id: string;
    title: string;
    updatedAt: number;
    messages: ChatSessionMessage[];
  }>;
  activeSessionId: string;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onDeleteSession: (id: string) => void;
};

export function AssistantPage({
  messages,
  loading,
  error,
  onSend,
  selectedMonth,
  months,
  onMonthChange,
  selectedCell,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}: Props) {
  const suggestions = [
    "Who is at highest burnout risk?",
    "Stress peak shift patterns",
    "What should a ward supervisor focus on this month?",
  ];

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h3>Chats</h3>
          <button type="button" onClick={onNewSession} className={styles.newChatButton}>
            New
          </button>
        </div>
        <div className={styles.sessionList}>
          {sessions.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => onSelectSession(s.id)}
              className={`${styles.sessionItem} ${s.id === activeSessionId ? styles.sessionItemActive : ""}`}
              title={s.title}
            >
              <span className={styles.sessionRow}>
                <span className={styles.sessionTitle}>{s.title}</span>
                <button
                  type="button"
                  className={styles.deleteChatButton}
                  title="Delete chat"
                  aria-label={`Delete chat ${s.title}`}
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const ok = window.confirm(`Delete chat "${s.title}"? This cannot be undone.`);
                    if (ok) onDeleteSession(s.id);
                  }}
                >
                  🗑
                </button>
              </span>
              <span className={styles.sessionMeta}>{new Date(s.updatedAt).toLocaleString()}</span>
            </button>
          ))}
        </div>
      </aside>

      <div className={styles.page}>
      <header className={styles.banner}>
        <div className={styles.bannerIdentity}>
          <div className={styles.botIcon}>CS</div>
          <div>
            <h2>Care-Sync Assistant</h2>
            <p>Clinical decision support · wearable stress intelligence</p>
          </div>
        </div>
        <div className={styles.bannerActions}>
          <label htmlFor="assistant-month" className={styles.monthLabel}>
            Month
          </label>
          <select
            id="assistant-month"
            value={selectedMonth}
            onChange={(e) => onMonthChange(e.target.value)}
            disabled={!months.length || loading}
          >
            {months.map((month) => (
              <option key={month} value={month}>
                {month}
              </option>
            ))}
          </select>
          <span className={styles.status}>
            <span className={styles.statusDot} />
            Online
          </span>
        </div>
      </header>

      <section className={styles.contextBar}>
        <div className={styles.chip}>
          <span className={styles.chipLabel}>Data month</span>
          <span className={styles.chipValue}>{selectedMonth || "-"}</span>
        </div>
        <div className={styles.chip}>
          <span className={styles.chipLabel}>Focus</span>
          <span className={styles.chipValue}>
            {selectedCell ? `Caregiver ${selectedCell.id}` : "General analysis"}
          </span>
        </div>
        <div className={styles.chip}>
          <span className={styles.chipLabel}>Context</span>
          <span className={styles.chipValue}>
            {selectedCell ? "Heatmap cell selected" : "Dashboard-wide"}
          </span>
        </div>
      </section>

      <ChatPanel
        messages={messages}
        loading={loading}
        error={error}
        onSend={onSend}
        suggestions={suggestions}
      />
      </div>
    </div>
  );
}
