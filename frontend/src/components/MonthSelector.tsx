import styles from "../styles/MonthSelector.module.css";

type Props = {
  month: string;
  months: string[];
  onChange: (month: string) => void;
};

export function MonthSelector({ month, months, onChange }: Props) {
  return (
    <div className={styles.wrapper}>
      <label htmlFor="month">Month</label>
      <select id="month" value={month} onChange={(e) => onChange(e.target.value)}>
        {months.map((m) => (
          <option key={m} value={m}>
            {m}
          </option>
        ))}
      </select>
    </div>
  );
}
