import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { getSensorRecords, sendChat } from "./api/backend";
import { DashboardLayout } from "./components/DashboardLayout";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleGuard } from "./auth/RoleGuard";
import type { ChatMessage } from "./components/ChatPanel";
import { AssistantPage } from "./pages/AssistantPage";
import { CaregiversPage } from "./pages/CaregiversPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { UserManagementPage } from "./pages/UserManagementPage";
import type { SensorRecord } from "./types";
import { getDistinctMonths } from "./utils/heatmap";

type SendMessageOverrides = {
  monthLabel?: string;
  selectedCaregiverId?: string;
  activeView?: string;
  heatmapCell?: Record<string, unknown> | null;
  sessionId?: string;
};

type ChatSession = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  messages: ChatMessage[];
};

const VISUALIZATION_CATALOG = [
  { id: "heatmap", label: "Stress Heatmap", path: "/", tab: "coverage" },
  { id: "coverage", label: "Coverage Chart", path: "/", tab: "coverage" },
  { id: "daily_pattern", label: "Daily Pattern Chart", path: "/", tab: "coverage" },
  { id: "comparison", label: "Comparison Chart", path: "/", tab: "comparison" },
  {
    id: "high_stress_contribution",
    label: "High Stress Contribution by Caregiver",
    path: "/",
    tab: "comparison",
  },
  { id: "signals", label: "Signal Relationships Chart", path: "/", tab: "signals" },
];

function toConciseAssistantReply(rawReply: string) {
  return rawReply
    .replace(/\r/g, "")
    .split("\n")
    .filter((line) => !line.trim().startsWith("**Provider:**"))
    .join("\n")
    .trim();
}

export default function App() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string>("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [selectedMonth, setSelectedMonth] = useState("");
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);
  const [selectedCell, setSelectedCell] = useState<SensorRecord | null>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;
  const messages = activeSession?.messages ?? [];

  function buildSession(title?: string): ChatSession {
    const now = Date.now();
    const id = `${now}-${Math.random().toString(16).slice(2)}`;
    return {
      id,
      title: title?.trim() || "New chat",
      createdAt: now,
      updatedAt: now,
      messages: [],
    };
  }

  function createSession(title?: string) {
    const session = buildSession(title);
    setSessions((prev) => [session, ...prev]);
    setActiveSessionId(session.id);
    return session;
  }

  function deleteSession(sessionId: string) {
    setSessions((prev) => {
      const remaining = prev.filter((s) => s.id !== sessionId);
      if (activeSessionId === sessionId) {
        const nextId = remaining[0]?.id;
        if (nextId) {
          setActiveSessionId(nextId);
          return remaining;
        }
        const fresh = buildSession("New chat");
        setActiveSessionId(fresh.id);
        return [fresh];
      }
      return remaining;
    });
  }

  useEffect(() => {
    try {
      const raw = localStorage.getItem("care-sync.chat.sessions.v1");
      const rawActive = localStorage.getItem("care-sync.chat.activeSessionId.v1") || "";
      const parsed = raw ? (JSON.parse(raw) as ChatSession[]) : [];
      if (Array.isArray(parsed) && parsed.length) {
        setSessions(parsed);
        const activeOk = parsed.some((s) => s.id === rawActive) ? rawActive : parsed[0].id;
        setActiveSessionId(activeOk);
      } else {
        const s = createSession("New chat");
        setActiveSessionId(s.id);
      }
    } catch {
      const s = createSession("New chat");
      setActiveSessionId(s.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    try {
      localStorage.setItem("care-sync.chat.sessions.v1", JSON.stringify(sessions));
      if (activeSessionId) {
        localStorage.setItem("care-sync.chat.activeSessionId.v1", activeSessionId);
      }
    } catch {
      // ignore storage failures
    }
  }, [sessions, activeSessionId]);

  useEffect(() => {
    let cancelled = false;
    async function bootstrapAssistantDefaults() {
      try {
        const baseline = await getSensorRecords();
        const months = getDistinctMonths(baseline);
        if (cancelled) return;
        setAvailableMonths((prev) => (prev.length ? prev : months));
        setSelectedMonth((prev) => prev || months[months.length - 1] || "");
      } catch {
        // If backend isn't up yet, we silently rely on Dashboard bootstrap later.
      }
    }
    bootstrapAssistantDefaults();
    return () => {
      cancelled = true;
    };
  }, []);

  async function sendMessage(message: string, overrides: SendMessageOverrides = {}) {
    const text = message.trim();
    if (!text) {
      setChatError("Please enter a message before sending.");
      return;
    }

    try {
      setChatLoading(true);
      setChatError("");
      let targetSessionId = overrides.sessionId ?? activeSessionId;
      if (!targetSessionId) {
        const s = createSession("New chat");
        targetSessionId = s.id;
      }
      setSessions((prev) => {
        const now = Date.now();
        const idx = prev.findIndex((s) => s.id === targetSessionId);
        if (idx < 0) return prev;
        const next = [...prev];
        const s = next[idx];
        next[idx] = { ...s, updatedAt: now, messages: [...s.messages, { role: "user", content: text }] };
        return next;
      });

      // Frontend calls backend /api/chat only; backend handles model keys and .env.
      const reply = await sendChat({
        message: text,
        ui_state: {
          month_label: overrides.monthLabel ?? selectedMonth,
          selected_caregiver_id:
            overrides.selectedCaregiverId ?? (selectedCell ? String(selectedCell.id) : undefined),
          active_view: overrides.activeView ?? "assistant",
          visualization_catalog: VISUALIZATION_CATALOG,
        },
        heatmap_cell:
          overrides.heatmapCell !== undefined ? overrides.heatmapCell : null,
      });

      setSessions((prev) => {
        const now = Date.now();
        const idx = prev.findIndex((s) => s.id === targetSessionId);
        if (idx < 0) return prev;
        const next = [...prev];
        const s = next[idx];
        next[idx] = {
          ...s,
          updatedAt: now,
          messages: [...s.messages, { role: "assistant", content: toConciseAssistantReply(reply) }],
        };
        return next;
      });
    } catch (err) {
      const fallback =
        "Unable to reach the assistant right now. Ensure backend is running and restart Flask after .env updates.";
      setChatError((err as Error)?.message || fallback);
    } finally {
      setChatLoading(false);
    }
  }

  async function askFromVisualization(args: {
    message: string;
    activeView: string;
    month?: string;
    caregiverId?: string;
    heatmapCell?: Record<string, unknown> | null;
    selectedCellRecord?: SensorRecord | null;
  }) {
    if (args.month) setSelectedMonth(args.month);
    if (args.selectedCellRecord !== undefined) {
      setSelectedCell(args.selectedCellRecord);
    }
    navigate("/assistant");
    // Start a fresh thread for a visualization-triggered ask.
    const monthTitle = args.month || selectedMonth || "All months";
    const who = args.caregiverId ? `Caregiver ${args.caregiverId}` : args.selectedCellRecord ? `Caregiver ${args.selectedCellRecord.id}` : "";
    const s = createSession([who, monthTitle].filter(Boolean).join(" · ") || "New chat");
    await sendMessage(args.message, {
      sessionId: s.id,
      monthLabel: args.month ?? selectedMonth,
      selectedCaregiverId: args.caregiverId,
      activeView: args.activeView,
      heatmapCell: args.heatmapCell,
    });
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route
          index
          element={
            <DashboardPage
              onAskAssistant={askFromVisualization}
              onMonthChange={setSelectedMonth}
              onAvailableMonthsChange={setAvailableMonths}
              onSelectedCellChange={setSelectedCell}
            />
          }
        />
        <Route path="caregivers" element={<CaregiversPage />} />
        <Route
          path="assistant"
          element={
            <AssistantPage
              messages={messages}
              loading={chatLoading}
              error={chatError}
              onSend={(message) => sendMessage(message)}
              selectedMonth={selectedMonth}
              months={availableMonths}
              onMonthChange={setSelectedMonth}
              selectedCell={selectedCell}
              sessions={sessions}
              activeSessionId={activeSessionId}
              onSelectSession={(id) => setActiveSessionId(id)}
              onNewSession={() => createSession("New chat")}
              onDeleteSession={(id) => deleteSession(id)}
            />
          }
        />
        <Route
          path="admin/users"
          element={
            <RoleGuard require="manage:users">
              <UserManagementPage />
            </RoleGuard>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
