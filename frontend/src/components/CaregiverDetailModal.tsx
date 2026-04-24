import type { Caregiver } from "../types";
import styles from "../styles/CaregiverDetailModal.module.css";

type Props = {
  open: boolean;
  caregiverId: string;
  caregiver: Caregiver | null;
  loading?: boolean;
  onClose: () => void;
};

function titleCase(input: string) {
  return (input || "")
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function preferredName(caregiver: Caregiver | null, fallbackId: string) {
  if (!caregiver) return `Caregiver ${fallbackId}`;
  const keys = Object.keys(caregiver);
  const nameKey = keys.find((k) => ["name", "full_name", "caregiver_name"].includes(k.toLowerCase()));
  if (nameKey && caregiver[nameKey] != null) {
    const v = String(caregiver[nameKey]).trim();
    if (v) return v;
  }
  return `Caregiver ${fallbackId}`;
}

function entriesForDetail(caregiver: Caregiver | null) {
  if (!caregiver) return [];
  const rows = Object.entries(caregiver)
    .map(([key, value]) => [key, value] as const)
    .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== "");

  // Keep "headline" fields first if present, then the rest alphabetically.
  const priority = ["id", "ID", "name", "role", "department", "shift", "experience", "certifications"];
  const score = (k: string) => {
    const idx = priority.findIndex((p) => p.toLowerCase() === k.toLowerCase());
    return idx === -1 ? 999 : idx;
  };

  return rows.sort(([a], [b]) => score(a) - score(b) || a.localeCompare(b));
}

function toneForKey(key: string) {
  const k = key.toLowerCase();
  if (k.includes("stress") || k.includes("label") || k.includes("high")) return "stress";
  if (k.includes("department") || k.includes("role")) return "role";
  if (k.includes("reading") || k.includes("sensor") || k.includes("shift")) return "work";
  return "identity";
}

export function CaregiverDetailModal({
  open,
  caregiverId,
  caregiver,
  loading = false,
  onClose,
}: Props) {
  if (!open) return null;

  const avatarText = String(caregiverId || "").slice(0, 2).toUpperCase() || "CG";
  const name = preferredName(caregiver, caregiverId);
  const rows = entriesForDetail(caregiver);

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <article className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <header className={styles.header}>
          <div className={styles.headerLeft}>
            <div className={styles.avatar}>{avatarText}</div>
            <div className={styles.identity}>
              <h3>{name}</h3>
              <p>
                Caregiver profile · ID <strong>{caregiverId}</strong>
              </p>
            </div>
          </div>
          <button className={styles.close} onClick={onClose} aria-label="Close popup">
            ×
          </button>
        </header>

        {loading ? (
          <div className={styles.loadingCard}>Loading caregiver details…</div>
        ) : caregiver ? (
          <section className={styles.grid}>
            {rows.map(([key, value]) => (
              <div key={key} className={`${styles.item} ${styles[toneForKey(key)]}`}>
                <span>{titleCase(key)}</span>
                <strong>{String(value)}</strong>
              </div>
            ))}
          </section>
        ) : (
          <div className={styles.loadingCard}>No caregiver detail available.</div>
        )}
      </article>
    </div>
  );
}

