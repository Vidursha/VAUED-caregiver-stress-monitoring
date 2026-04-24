import styles from "../styles/DashboardCharts.module.css";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type DailyPatternPoint = {
  date: string;
  highShare: number;
  readings: number;
  highCount?: number;
  lowCount?: number;
  mediumCount?: number;
};

type Props = {
  month: string;
  data: DailyPatternPoint[];
  onAskAi: () => void;
};

export function DailyPatternChart({ month, data, onAskAi }: Props) {
  if (!data.length) return null;

  const insight = (() => {
    const sorted = [...data].sort((a, b) => b.highShare - a.highShare);
    const peak = sorted[0];
    const lowest = sorted[sorted.length - 1];
    return `Peak high-stress day: ${peak.date} (${peak.highShare.toFixed(1)}%). Lowest: ${lowest.date} (${lowest.highShare.toFixed(1)}%).`;
  })();

  return (
    <section className={styles.chartCard}>
      <div className={styles.chartHeader}>
        <div>
          <h3>Daily pattern - {month}</h3>
          <p>Line = high-stress share by day. Bars = number of readings.</p>
        </div>
        <button className={styles.askButton} onClick={onAskAi}>
          Ask AI
        </button>
      </div>

      <div className={styles.rechartsWrap}>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={data} margin={{ top: 10, right: 18, left: 8, bottom: 10 }}>
            <CartesianGrid stroke="#e8eef5" strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tick={{ fill: "#5b748c", fontSize: 12 }}
              axisLine={{ stroke: "#d7e2ee" }}
              tickLine={{ stroke: "#d7e2ee" }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: "#5b748c", fontSize: 12 }}
              axisLine={{ stroke: "#d7e2ee" }}
              tickLine={{ stroke: "#d7e2ee" }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tick={{ fill: "#5b748c", fontSize: 12 }}
              axisLine={{ stroke: "#d7e2ee" }}
              tickLine={{ stroke: "#d7e2ee" }}
            />
            <Tooltip
              content={(props: any) => {
                const { active, payload, label } = props;
                if (!active || !payload?.length) return null;
                const row = payload[0].payload as DailyPatternPoint;
                return (
                  <div className={styles.tooltip}>
                    <div className={styles.tooltipTitle}>{label}</div>
                    <div className={styles.tooltipRow}>
                      <span className={styles.dot} style={{ background: "#40B3AF" }} />
                      <span>Total readings:</span>
                      <strong>{row.readings}</strong>
                    </div>
                    <div className={styles.tooltipRow}>
                      <span className={styles.dot} style={{ background: "#b07a86" }} />
                      <span>High-stress share:</span>
                      <strong>{row.highShare.toFixed(1)}%</strong>
                    </div>
                    {typeof row.highCount === "number" ? (
                      <div className={styles.tooltipRow}>
                        <span className={styles.dot} style={{ background: "#ef4444" }} />
                        <span>High count:</span>
                        <strong>{row.highCount}</strong>
                      </div>
                    ) : null}
                    {typeof row.lowCount === "number" ? (
                      <>
                        <div className={styles.tooltipDivider} />
                        <div className={styles.tooltipRow}>
                          <span className={styles.dot} style={{ background: "#22c55e" }} />
                          <span>Low:</span>
                          <strong>{row.lowCount}</strong>
                        </div>
                        <div className={styles.tooltipRow}>
                          <span className={styles.dot} style={{ background: "#f59e0b" }} />
                          <span>Medium:</span>
                          <strong>{row.mediumCount ?? 0}</strong>
                        </div>
                        <div className={styles.tooltipRow}>
                          <span className={styles.dot} style={{ background: "#ef4444" }} />
                          <span>High:</span>
                          <strong>{row.highCount ?? 0}</strong>
                        </div>
                      </>
                    ) : null}
                  </div>
                );
              }}
              cursor={{ fill: "rgba(148, 163, 184, 0.12)" }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ paddingBottom: 6 }}
              formatter={(value) => <span style={{ color: "#4c657e", fontSize: 12 }}>{value}</span>}
            />
            <Bar
              yAxisId="left"
              dataKey="readings"
              name="Readings"
              fill="#2f7f77"
              radius={[8, 8, 0, 0]}
              barSize={18}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="highShare"
              name="High-stress share"
              stroke="#b07a86"
              strokeWidth={2.5}
              dot={{ r: 2.5 }}
              activeDot={{ r: 4 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <ul className={styles.insights}>
        <li>{insight}</li>
        <li>
          Selected month insight ({month}): high-stress share trend can be compared with readings
          volume spikes to detect potential anomalies.
        </li>
      </ul>
    </section>
  );
}
 