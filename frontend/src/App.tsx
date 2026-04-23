import { useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { sendChat } from "./api/backend";
import { Layout } from "./components/Layout";
import type { ChatMessage } from "./components/ChatPanel";
import { AssistantPage } from "./pages/AssistantPage";
import { CaregiversPage } from "./pages/CaregiversPage";
import { DashboardPage } from "./pages/DashboardPage";
import type { SensorRecord } from "./types";

type SendMessageOverrides = {
  monthLabel?: string;
  selectedCaregiverId?: string;
  activeView?: string;
  heatmapCell?: Record<string, unknown> | null;
};

function toConciseAssistantReply(rawReply: string) {
  const lowerRaw = rawReply.toLowerCase();
  const isOutOfScope =
    lowerRaw.includes("outside the scope") ||
    lowerRaw.includes("not suitable for this dataset") ||
    lowerRaw.includes("only help with") ||
    (lowerRaw.includes("off-topic") && lowerRaw.includes("dataset"));

  if (isOutOfScope) {
    return [
      "- This question is outside the scope of the caregiver stress dataset.",
      "- I can assist with stress analysis, sensor signals (EDA, HR, TEMP, movement), and dashboard insights.",
      "- Try asking about a caregiver trend, a month pattern, or a chart interpretation.",
    ].join("\n");
  }

  const cleaned = rawReply
    .replace(/\r/g, "")
    .split("\n")
    .map((line) => line.trim())
    .filter(
      (line) =>
        line &&
        !line.startsWith("###") &&
        !line.startsWith("##") &&
        !line.startsWith("**Provider:**") &&
        line !== "---",
    );

  const explicitBullets = cleaned
    .map((line) => line.replace(/^[-*•]\s+/, "").trim())
    .filter((line) => line.length > 4);

  const source = explicitBullets.length
    ? explicitBullets
    : cleaned
        .join(" ")
        .split(/[.?!]\s+/)
        .map((s) => s.trim())
        .filter((s) => s.length > 10);

  const trimmed = source
    .map((line) => line.replace(/\*\*/g, "").replace(/\s+/g, " ").trim())
    .filter(
      (line) =>
        !/^context[:]?$/i.test(line) &&
        !/^you asked[:]?$/i.test(line) &&
        !/^dataset digest/i.test(line),
    )
    .slice(0, 6);

  const bullets = (trimmed.length ? trimmed : ["No clear summary was returned. Please ask again."])
    .map((line) => `- ${line}`);
  return bullets.join("\n");
}

export default function App() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [selectedMonth, setSelectedMonth] = useState("");
  const [availableMonths, setAvailableMonths] = useState<string[]>([]);
  const [selectedCell, setSelectedCell] = useState<SensorRecord | null>(null);

  async function sendMessage(message: string, overrides: SendMessageOverrides = {}) {
    const text = message.trim();
    if (!text) {
      setChatError("Please enter a message before sending.");
      return;
    }

    try {
      setChatLoading(true);
      setChatError("");
      setMessages((prev) => [...prev, { role: "user", content: text }]);

      // Frontend calls backend /api/chat only; backend handles model keys and .env.
      const reply = await sendChat({
        message: text,
        ui_state: {
          month_label: overrides.monthLabel ?? selectedMonth,
          selected_caregiver_id:
            overrides.selectedCaregiverId ?? (selectedCell ? String(selectedCell.id) : undefined),
          active_view: overrides.activeView ?? "assistant",
        },
        heatmap_cell:
          overrides.heatmapCell ?? (selectedCell as unknown as Record<string, unknown> | null),
      });

      setMessages((prev) => [...prev, { role: "assistant", content: toConciseAssistantReply(reply) }]);
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
    await sendMessage(args.message, {
      monthLabel: args.month ?? selectedMonth,
      selectedCaregiverId: args.caregiverId,
      activeView: args.activeView,
      heatmapCell: args.heatmapCell,
    });
  }

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
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
            />
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
