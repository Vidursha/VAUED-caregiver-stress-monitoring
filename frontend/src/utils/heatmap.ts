import type { SensorRecord } from "../types";

export type HeatmapCell = {
  caregiverId: string;
  date: string;
  record?: SensorRecord;
};

export function monthFromRecord(record: SensorRecord) {
  const dt = String(record.datetime ?? "");
  if (dt.length >= 8) {
    const month = dt.slice(3, 5);
    const year = dt.slice(6, 8);
    return `20${year}-${month}`;
  }
  return "";
}

export function getDistinctMonths(records: SensorRecord[]) {
  return [...new Set(records.map(monthFromRecord).filter(Boolean))].sort();
}

export function buildHeatmap(records: SensorRecord[]) {
  const caregivers = [...new Set(records.map((r) => String(r.id)))].sort();
  const dates = [...new Set(records.map((r) => String(r.date)))].sort();
  const map = new Map<string, SensorRecord>();

  for (const rec of records) {
    map.set(`${rec.id}|${rec.date}`, rec);
  }

  const cells: HeatmapCell[] = [];
  for (const caregiverId of caregivers) {
    for (const date of dates) {
      cells.push({
        caregiverId,
        date,
        record: map.get(`${caregiverId}|${date}`),
      });
    }
  }

  return { caregivers, dates, cells };
}

export function colorByLabel(label?: number) {
  if (label === 0) return "#22c55e";
  if (label === 1) return "#f59e0b";
  if (label === 2) return "#ef4444";
  return "#e3e8ee";
}
