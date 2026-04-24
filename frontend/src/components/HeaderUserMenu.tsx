import { useEffect, useRef, useState } from "react";
import { LogOut, Settings, UserCircle2 } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import styles from "../styles/HeaderUserMenu.module.css";

export function HeaderUserMenu() {
  const { state, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!ref.current) return;
      if (e.target instanceof Node && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  if (state.status !== "authenticated") return null;

  const initials = state.user.name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");

  return (
    <div className={styles.wrap} ref={ref}>
      <button className={styles.trigger} type="button" onClick={() => setOpen((v) => !v)}>
        <span className={styles.avatar}>{initials || "WM"}</span>
        <span className={styles.meta}>
          <strong>{state.user.name}</strong>
          <span>{state.user.role}</span>
        </span>
        <UserCircle2 size={18} className={styles.icon} />
      </button>

      {open ? (
        <div className={styles.menu} role="menu" aria-label="User menu">
          <button type="button" className={styles.item} onClick={() => setOpen(false)}>
            <Settings size={16} />
            Profile / settings
          </button>
          <button type="button" className={styles.itemDanger} onClick={logout}>
            <LogOut size={16} />
            Logout
          </button>
        </div>
      ) : null}
    </div>
  );
}

