import { useEffect, useMemo, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import type { Role, StoredUser } from "../auth/types";
import styles from "../styles/UserFormModal.module.css";

const ROLES: Role[] = ["Admin", "Ward Manager", "Doctor", "Nurse", "Viewer"];

type Props = {
  open: boolean;
  initial?: StoredUser | null;
  onClose: () => void;
  onSave: (user: StoredUser) => void;
};

function uid() {
  return `u_${Math.random().toString(16).slice(2)}_${Date.now().toString(16)}`;
}

export function UserFormModal({ open, initial, onClose, onSave }: Props) {
  const isEdit = Boolean(initial);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("Viewer");
  const [active, setActive] = useState(true);
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open) return;
    setError("");
    setName(initial?.name ?? "");
    setEmail(initial?.email ?? "");
    setRole((initial?.role as Role) ?? "Viewer");
    setActive(initial?.active ?? true);
    setPassword(initial?.password ?? "");
    setShowPassword(false);
  }, [open, initial]);

  const canSave = useMemo(() => {
    if (!name.trim() || !email.trim()) return false;
    if (!isEdit && password.trim().length < 4) return false;
    return true;
  }, [name, email, password, isEdit]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const n = name.trim();
    const em = email.trim().toLowerCase();
    if (!n || !em) {
      setError("Name and email are required.");
      return;
    }
    if (!isEdit && password.trim().length < 4) {
      setError("Password must be at least 4 characters for mock login.");
      return;
    }
    const next: StoredUser = {
      id: initial?.id ?? uid(),
      name: n,
      email: em,
      role,
      active,
      password: password.trim() || initial?.password || "",
    };
    onSave(next);
    onClose();
  }

  if (!open) return null;

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <article className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <header className={styles.header}>
          <div>
            <h3>{isEdit ? "Edit user" : "Add user"}</h3>
            <p>Admin-only · mock directory for development</p>
          </div>
          <button className={styles.close} onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>

        <form className={styles.form} onSubmit={submit}>
          <label className={styles.label}>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Ward Manager" />
          </label>

          <label className={styles.label}>
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="e.g. user@hospital.com" />
          </label>

          <div className={styles.grid2}>
            <label className={styles.label}>
              Role
              <select value={role} onChange={(e) => setRole(e.target.value as Role)}>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>

            <label className={styles.checkbox}>
              <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
              Active account
            </label>
          </div>

          <label className={styles.label}>
            Password {isEdit ? <span className={styles.subtle}>(mock)</span> : null}
            <div className={styles.passwordRow}>
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Set a mock password"
                type={showPassword ? "text" : "password"}
              />
              <button
                type="button"
                className={styles.iconButton}
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </label>

          {error ? <div className={styles.error}>{error}</div> : null}

          <footer className={styles.actions}>
            <button type="button" className={styles.secondary} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className={styles.primary} disabled={!canSave}>
              Save
            </button>
          </footer>
        </form>
      </article>
    </div>
  );
}

