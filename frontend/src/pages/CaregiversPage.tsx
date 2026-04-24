import { useEffect, useMemo, useState } from "react";
import { getCaregiverDetail, getCaregivers } from "../api/backend";
import { CaregiverDetailModal } from "../components/CaregiverDetailModal";
import { CaregiverTable } from "../components/CaregiverTable";
import type { Caregiver } from "../types";
import styles from "../styles/Page.module.css";

export function CaregiversPage() {
  const [caregivers, setCaregivers] = useState<Caregiver[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [selectedDetail, setSelectedDetail] = useState<Caregiver | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadCaregivers() {
      try {
        setLoading(true);
        const data = await getCaregivers();
        setCaregivers(data);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    }
    loadCaregivers();
  }, []);

  useEffect(() => {
    async function loadDetail() {
      if (!selectedId) {
        setSelectedDetail(null);
        setModalOpen(false);
        return;
      }
      try {
        setDetailLoading(true);
        const detail = await getCaregiverDetail(selectedId);
        setSelectedDetail(detail);
        setModalOpen(true);
      } catch (err) {
        setError((err as Error).message);
        setModalOpen(true);
      } finally {
        setDetailLoading(false);
      }
    }
    loadDetail();
  }, [selectedId]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return caregivers;
    return caregivers.filter((row) =>
      Object.values(row).some((v) => String(v ?? "").toLowerCase().includes(q)),
    );
  }, [caregivers, query]);

  return (
    <div className={styles.page}>
      <header className={styles.headerRow}>
        <div className={styles.headerColumn}>
          <h2>Caregivers</h2>
          <p className={styles.subtitle}>Profile overview linked with stress monitoring records.</p>
        </div>
        <div className={styles.filterBar}>
          <input
            className={styles.search}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search name, role, department..."
          />
          <span className={styles.resultText}>
            Showing {filtered.length} of {caregivers.length}
          </span>
        </div>
      </header>

      {loading ? <p>Loading caregivers...</p> : null}
      {error ? <p className={styles.error}>{error}</p> : null}

      <CaregiverTable caregivers={filtered} selectedId={selectedId} onSelect={setSelectedId} />

      <CaregiverDetailModal
        open={modalOpen}
        caregiverId={selectedId}
        caregiver={selectedDetail}
        loading={detailLoading}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
}
