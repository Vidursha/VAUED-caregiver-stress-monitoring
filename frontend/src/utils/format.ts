export function toFixed(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "-";
  }
  return Number(value).toFixed(digits);
}

export function labelText(label: number) {
  if (label === 0) return "Low";
  if (label === 1) return "Medium";
  if (label === 2) return "High";
  return "Unknown";
}

export function stressIndexFromLabel(label: number) {
  if (label === 0) return 33;
  if (label === 1) return 67;
  if (label === 2) return 100;
  return 0;
}
