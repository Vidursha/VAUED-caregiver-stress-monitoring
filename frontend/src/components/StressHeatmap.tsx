import type { SensorRecord } from "../types";
import { buildHeatmap, colorByLabel } from "../utils/heatmap";
import styles from "../styles/StressHeatmap.module.css";

type Props = {
  records: SensorRecord[];
  onCellClick: (record: SensorRecord) => void;
  onAskAi: () => void;
};

export function StressHeatmap({ records, onCellClick, onAskAi }: Props) {
  const { caregivers, dates, cells } = buildHeatmap(records);

  if (!records.length) {
    return <p className={styles.empty}>No sensor records found for this month.</p>;
  }

  return (
    <section className={styles.wrapper}>
      <div className={styles.top}>
        <div>
          <h3>Stress heatmap</h3>
          <p>Daily stress label by caregiver ID for the selected month (click any colored cell).</p>
        </div>
        <button className={styles.askButton} onClick={onAskAi}>
          Ask AI
        </button>
      </div>
      <div className={styles.scroll}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Caregiver ID</th>
              {dates.map((date) => (
                <th key={date}>{date}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {caregivers.map((caregiverId) => (
              <tr key={caregiverId}>
                <th>{caregiverId}</th>
                {dates.map((date) => {
                  const cell = cells.find(
                    (entry) => entry.caregiverId === caregiverId && entry.date === date,
                  );
                  const record = cell?.record;
                  const label = record?.label;
                  return (
                    <td
                      key={`${caregiverId}-${date}`}
                      style={{ background: colorByLabel(label) }}
                      className={record ? styles.clickable : ""}
                      onClick={() => {
                        if (record) onCellClick(record);
                      }}
                      title={record ? `Label ${label}` : "No reading"}
                    />
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className={styles.legend}>
        <span><i style={{ background: colorByLabel(0) }} />Low</span>
        <span><i style={{ background: colorByLabel(1) }} />Medium</span>
        <span><i style={{ background: colorByLabel(2) }} />High</span>
        <span><i style={{ background: colorByLabel(undefined) }} />No reading</span>
      </div>
    </section>
  );
}
