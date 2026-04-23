import type { Caregiver } from "../types";
import styles from "../styles/CaregiverTable.module.css";

type Props = {
  caregivers: Caregiver[];
  selectedId: string;
  onSelect: (id: string) => void;
};

function pick(
  caregiver: Caregiver,
  candidates: string[],
  fallback = "-",
): string {
  for (const key of candidates) {
    const match = Object.keys(caregiver).find((k) => k.toLowerCase() === key.toLowerCase());
    if (match && caregiver[match] !== null && caregiver[match] !== undefined) {
      const value = String(caregiver[match]).trim();
      if (value) return value;
    }
  }
  return fallback;
}

export function CaregiverTable({ caregivers, selectedId, onSelect }: Props) {
  if (!caregivers.length) {
    return <p className={styles.empty}>No caregivers found.</p>;
  }

  return (
    <div className={styles.wrapper}>
      {caregivers.map((caregiver) => {
        const id = String(caregiver.ID ?? caregiver.id ?? "");
        const name = pick(caregiver, ["name", "full_name", "caregiver_name"], `Caregiver ${id}`);
        const role = pick(caregiver, ["role", "job_role", "position"]);
        const department = pick(caregiver, ["department", "specialty", "unit"]);
        const shift = pick(caregiver, ["shift", "work_shift", "duty_shift"]);
        const experience = pick(caregiver, ["years_experience", "experience", "exp_years"], "-");

        return (
          <article
            key={id}
            className={`${styles.card} ${id === selectedId ? styles.selected : ""}`}
            onClick={() => onSelect(id)}
          >
            <div className={styles.cardTop}>
              <span className={styles.badge}>{String(id).slice(0, 2).toUpperCase()}</span>
              <span className={styles.idChip}>ID {id}</span>
            </div>

            <h3>{name}</h3>

            <div className={styles.pills}>
              <span className={`${styles.pill} ${styles.role}`}>{role}</span>
              <span className={`${styles.pill} ${styles.dept}`}>{department}</span>
              <span className={`${styles.pill} ${styles.shift}`}>{shift}</span>
            </div>

            <p className={styles.experience}>Experience: {experience} year(s)</p>

            <div className={styles.tags}>
              <span>Stress-aware monitoring</span>
              <span>Wearable-linked</span>
            </div>
          </article>
        );
      })}
    </div>
  );
}
