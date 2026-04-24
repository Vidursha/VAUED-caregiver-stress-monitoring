import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getSensorRecords } from "../api/backend";
import { ComparisonChart } from "../components/ComparisonChart";
import { CoverageChart, type CoverageMonthPoint } from "../components/CoverageChart";
import { DailyPatternChart, type DailyPatternPoint } from "../components/DailyPatternChart";
import { HighStressContributionChart } from "../components/HighStressContributionChart";
import { KpiCards } from "../components/KpiCards";
import { MonthSelector } from "../components/MonthSelector";
import { SignalRelationshipsChart } from "../components/SignalRelationshipsChart";
import { SensorModal } from "../components/SensorModal";
import { StressHeatmap } from "../components/StressHeatmap";
import type { SensorRecord } from "../types";
import { getDistinctMonths, monthFromRecord } from "../utils/heatmap";
import styles from "../styles/Page.module.css";
import chartStyles from "../styles/DashboardCharts.module.css";

type Props = {
  onAskAssistant: (args: {
    message: string;
    activeView: string;
    month?: string;
    caregiverId?: string;
    heatmapCell?: Record<string, unknown> | null;
    selectedCellRecord?: SensorRecord | null;
  }) => Promise<void>;
  onMonthChange: (month: string) => void;
  onAvailableMonthsChange: (months: string[]) => void;
  onSelectedCellChange: (record: SensorRecord | null) => void;
};

export function DashboardPage({
  onAskAssistant,
  onMonthChange,
  onAvailableMonthsChange,
  onSelectedCellChange,
}: Props) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tab, setTab] = useState<"coverage" | "comparison" | "signals">("coverage");
  const [allRecords, setAllRecords] = useState<SensorRecord[]>([]);
  const [records, setRecords] = useState<SensorRecord[]>([]);
  const [month, setMonth] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<SensorRecord | null>(null);
  const [selectedCoverageMonth, setSelectedCoverageMonth] = useState<string | null>(null);
  const [comparisonMonth, setComparisonMonth] = useState<string>("");
  const [donutMonth, setDonutMonth] = useState<string>("");

  useEffect(() => {
    const viz = (searchParams.get("viz") || "").trim();
    const qsMonth = (searchParams.get("month") || "").trim();
    if (qsMonth) {
      setMonth(qsMonth);
      setComparisonMonth(qsMonth);
      setDonutMonth(qsMonth);
      setSelectedCoverageMonth(qsMonth);
    }
    if (viz === "comparison" || viz === "high_stress_contribution") setTab("comparison");
    if (viz === "signals") setTab("signals");
    if (viz === "coverage" || viz === "daily_pattern" || viz === "heatmap") setTab("coverage");

    if (viz) {
      // Clear params after applying so refresh doesn't keep jumping.
      setSearchParams({}, { replace: true });
      // Best-effort scroll after DOM paint.
      window.setTimeout(() => {
        const el = document.getElementById(`viz-${viz}`);
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 60);
    }
  }, []);

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoading(true);
        const baseline = await getSensorRecords();
        setAllRecords(baseline);
        const months = getDistinctMonths(baseline);
        const fallbackMonth = months[months.length - 1] ?? "";
        setMonth(fallbackMonth);
        onMonthChange(fallbackMonth);
        setComparisonMonth(fallbackMonth);
        setDonutMonth(fallbackMonth);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    bootstrap();
  }, []);

  useEffect(() => {
    async function loadMonthData() {
      if (!month) return;
      try {
        setLoading(true);
        const monthRecords = await getSensorRecords(month);
        setRecords(monthRecords);
        setError("");
        onMonthChange(month);
        setSelectedCoverageMonth(null);
        setComparisonMonth((prev) => prev || month);
        setDonutMonth((prev) => prev || month);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    loadMonthData();
  }, [month]);

  const months = useMemo(() => getDistinctMonths(allRecords), [allRecords]);

  useEffect(() => {
    onAvailableMonthsChange(months);
  }, [months, onAvailableMonthsChange]);

  const kpis = useMemo(() => {
    if (!records.length) {
      return {
        caregivers: 0,
        averageTemperature: null,
        stressIndex: null,
        averageHeartRate: null,
      };
    }
    const caregivers = new Set(records.map((r) => String(r.id))).size;
    const avgTemp = records.reduce((sum, r) => sum + Number(r.TEMP), 0) / records.length;
    const avgHr = records.reduce((sum, r) => sum + Number(r.HR), 0) / records.length;
    const avgLabel = records.reduce((sum, r) => sum + Number(r.label), 0) / records.length;
    return {
      caregivers,
      averageTemperature: avgTemp,
      stressIndex: (avgLabel / 2) * 100,
      averageHeartRate: avgHr,
    };
  }, [records]);

  const coverageData = useMemo<CoverageMonthPoint[]>(() => {
    const grouped = new Map<string, CoverageMonthPoint>();
    for (const record of allRecords) {
      const ym = monthFromRecord(record);
      if (!ym) continue;
      if (!grouped.has(ym)) {
        grouped.set(ym, { month: ym, low: 0, medium: 0, high: 0, total: 0 });
      }
      const entry = grouped.get(ym)!;
      entry.total += 1;
      if (Number(record.label) === 0) entry.low += 1;
      if (Number(record.label) === 1) entry.medium += 1;
      if (Number(record.label) === 2) entry.high += 1;
    }
    return [...grouped.values()].sort((a, b) => a.month.localeCompare(b.month));
  }, [allRecords]);

  const dailyPattern = useMemo<DailyPatternPoint[]>(() => {
    if (!selectedCoverageMonth) return [];
    const grouped = new Map<string, { total: number; high: number; low: number; medium: number }>();
    for (const record of allRecords) {
      if (monthFromRecord(record) !== selectedCoverageMonth) continue;
      const date = String(record.date);
      if (!grouped.has(date)) grouped.set(date, { total: 0, high: 0, low: 0, medium: 0 });
      const bucket = grouped.get(date)!;
      bucket.total += 1;
      const label = Number(record.label);
      if (label === 0) bucket.low += 1;
      if (label === 1) bucket.medium += 1;
      if (label === 2) bucket.high += 1;
    }
    return [...grouped.entries()]
      .map(([date, v]) => ({
        date,
        readings: v.total,
        highShare: v.total ? (v.high / v.total) * 100 : 0,
        highCount: v.high,
        lowCount: v.low,
        mediumCount: v.medium,
      }))
      .sort((a, b) => a.date.localeCompare(b.date));
  }, [allRecords, selectedCoverageMonth]);

  async function askAiAboutCell() {
    if (!selected) return;
    try {
      await onAskAssistant({
        message: `Why was caregiver ${selected.id} classified as ${Number(selected.label) === 2 ? "High" : Number(selected.label) === 1 ? "Medium" : "Low"} stress for this reading?`,
        activeView: "sensor_modal",
        month,
        caregiverId: String(selected.id),
        heatmapCell: selected as unknown as Record<string, unknown>,
        selectedCellRecord: selected,
      });
      setSelected(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className={styles.page}>
      <header className={styles.headerRow}>
        <div className={styles.headerColumn}>
          <h2>Dashboard</h2>
          <p className={styles.subtitle}>Stress intelligence overview from wearable sensor readings.</p>
        </div>
        <MonthSelector month={month} months={months} onChange={setMonth} />
      </header>

      {loading ? <p>Loading dashboard...</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}

      <KpiCards {...kpis} />
      <div id="viz-heatmap">
        <StressHeatmap
        records={records}
        onAskAi={() =>
          onAskAssistant({
            message: `Explain the main stress pattern in the heatmap for ${month}.`,
            activeView: "heatmap",
            month,
            selectedCellRecord: selected,
          })
        }
        onCellClick={(record) => {
          setSelected(record);
          onSelectedCellChange(record);
        }}
        />
      </div>

      <div className={chartStyles.tabSection}>
        <div>
          <h3 className={chartStyles.tabTitle}>Tabbed analytics workspace</h3>
          <p className={chartStyles.tabSubtitle}>
            Switch between coverage trends, stress-level comparisons, and signal relationships.
          </p>
        </div>
        <div className={chartStyles.tabBar}>
        <button
          className={`${chartStyles.tab} ${tab === "coverage" ? chartStyles.tabActive : ""}`}
          onClick={() => setTab("coverage")}
          type="button"
        >
          Coverage
        </button>
        <button
          className={`${chartStyles.tab} ${tab === "comparison" ? chartStyles.tabActive : ""}`}
          onClick={() => setTab("comparison")}
          type="button"
        >
          Comparison
        </button>
        <button
          className={`${chartStyles.tab} ${tab === "signals" ? chartStyles.tabActive : ""}`}
          onClick={() => setTab("signals")}
          type="button"
        >
          Signal relationships
        </button>
        </div>
      </div>

      {tab === "coverage" ? (
        <div className={chartStyles.tabPanel}>
          <div id="viz-coverage">
            <CoverageChart
            data={coverageData}
            selectedMonth={selectedCoverageMonth}
            onSelectMonth={setSelectedCoverageMonth}
            onAskAi={() =>
              onAskAssistant({
                message:
                  "Summarize the monthly stress distribution and identify the most critical month for a ward supervisor.",
                activeView: "coverage",
                month,
              })
            }
            />
          </div>
          {selectedCoverageMonth ? (
            <div id="viz-daily_pattern">
              <DailyPatternChart
              month={selectedCoverageMonth}
              data={dailyPattern}
              onAskAi={() =>
                onAskAssistant({
                  message: `Explain the daily stress pattern for ${selectedCoverageMonth} and highlight unusual days for a ward supervisor.`,
                  activeView: "daily_pattern",
                  month: selectedCoverageMonth,
                })
              }
              />
            </div>
          ) : null}
        </div>
      ) : null}

      {tab === "comparison" ? (
        <div className={chartStyles.tabPanel}>
          <div id="viz-comparison">
            <ComparisonChart
            allRecords={allRecords}
            month={comparisonMonth || month}
            months={months}
            onMonthChange={setComparisonMonth}
            onAskAi={(selectedMonth) =>
              onAskAssistant({
                message:
                  "Compare HR, EDA, temperature, and movement across stress levels for this month and explain what matters most for a ward supervisor.",
                activeView: "comparison",
                month: selectedMonth,
              })
            }
            />
          </div>
          <div id="viz-high_stress_contribution">
            <HighStressContributionChart
            allRecords={allRecords}
            month={donutMonth || month}
            onMonthChange={setDonutMonth}
            onAskAi={() =>
              onAskAssistant({
                message: `Explain the high-stress contribution by caregiver for ${donutMonth || month} and what a ward supervisor should pay attention to.`,
                activeView: "high_stress_contribution",
                month: donutMonth || month,
              })
            }
            />
          </div>
        </div>
      ) : null}

      {tab === "signals" ? (
        <div className={chartStyles.tabPanel}>
          <div id="viz-signals">
            <SignalRelationshipsChart
            allRecords={allRecords}
            month={month}
            months={months}
            onMonthChange={setMonth}
            onAskAi={(selectedMonth) =>
              onAskAssistant({
                message:
                  "Explain the relationship between heart rate, EDA, movement, and stress level for this month in plain language for a ward supervisor.",
                activeView: "signal_relationships",
                month: selectedMonth,
              })
            }
            />
          </div>
        </div>
      ) : null}

      <SensorModal
        record={selected}
        onClose={() => {
          setSelected(null);
          onSelectedCellChange(null);
        }}
        onAskAi={askAiAboutCell}
      />
    </div>
  );
}
