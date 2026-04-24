import styles from "../styles/AppLoadingScreen.module.css";
import { HeartPulse, Hospital } from "lucide-react";

export function AppLoadingScreen() {
  return (
    <div className={styles.page} role="status" aria-live="polite" aria-label="Loading dashboard">
      <div className={styles.card}>
        <div className={styles.symbolWrap}>
          <div className={styles.glow} />
          <div className={styles.badge}>
            <Hospital size={20} />
            <HeartPulse size={18} />
          </div>
        </div>
        <div className={styles.ring} />
        <h2>Preparing dashboard</h2>
        <p>Connecting caregiving insights and ward analytics...</p>
      </div>
    </div>
  );
}

