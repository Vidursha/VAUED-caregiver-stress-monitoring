import { useMemo, useState } from "react";
import { Pencil, Plus, Search, ShieldCheck, ToggleLeft, ToggleRight } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import type { StoredUser } from "../auth/types";
import { UserFormModal } from "../components/UserFormModal";
import styles from "../styles/UserManagement.module.css";

function sortUsers(users: StoredUser[]) {
  return [...users].sort((a, b) => a.name.localeCompare(b.name));
}

export function UserManagementPage() {
  const { users, upsertUser, setUserActive } = useAuth();
  const [query, setQuery] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<StoredUser | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const source = sortUsers(users);
    if (!q) return source;
    return source.filter((u) =>
      [u.name, u.email, u.role, u.active ? "active" : "inactive"].some((v) => v.toLowerCase().includes(q)),
    );
  }, [users, query]);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h2>User management</h2>
          <p>Admin controls for role-based access, account lifecycle, and dashboard permissions.</p>
        </div>
        <button
          className={styles.addBtn}
          onClick={() => {
            setEditing(null);
            setModalOpen(true);
          }}
        >
          <Plus size={16} />
          Add user
        </button>
      </header>

      <section className={styles.tools}>
        <div className={styles.searchBox}>
          <Search size={15} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name, email, role, or status"
          />
        </div>
        <span className={styles.count}>Showing {filtered.length} users</span>
      </section>

      <section className={styles.grid}>
        {filtered.map((user) => (
          <article className={styles.card} key={user.id}>
            <div className={styles.cardHead}>
              <div className={styles.avatar}>{user.name.slice(0, 2).toUpperCase()}</div>
              <div>
                <h4>{user.name}</h4>
                <p>{user.email}</p>
              </div>
            </div>

            <div className={styles.metaRow}>
              <span className={styles.rolePill}>
                <ShieldCheck size={14} />
                {user.role}
              </span>
              <span className={user.active ? styles.active : styles.inactive}>
                {user.active ? "Active" : "Inactive"}
              </span>
            </div>

            <div className={styles.actions}>
              <button
                className={styles.action}
                onClick={() => {
                  setEditing(user);
                  setModalOpen(true);
                }}
              >
                <Pencil size={14} />
                Edit
              </button>
              <button className={styles.action} onClick={() => setUserActive(user.id, !user.active)}>
                {user.active ? <ToggleRight size={14} /> : <ToggleLeft size={14} />}
                {user.active ? "Deactivate" : "Activate"}
              </button>
            </div>
          </article>
        ))}
      </section>

      <UserFormModal
        open={modalOpen}
        initial={editing}
        onClose={() => setModalOpen(false)}
        onSave={(user) => upsertUser(user)}
      />
    </div>
  );
}

