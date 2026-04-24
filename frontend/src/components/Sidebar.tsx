import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import styles from "../styles/Sidebar.module.css";

const links = [
  { to: "/", label: "Dashboard", perm: "view:dashboard" as const },
  { to: "/caregivers", label: "Caregivers", perm: "view:caregivers" as const },
  { to: "/assistant", label: "Assistant", perm: "view:assistant" as const },
  { to: "/admin/users", label: "User management", perm: "manage:users" as const },
];

export function Sidebar() {
  const { can, state } = useAuth();
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <h1>Care-Sync</h1>
        <p>Stress Intelligence</p>
      </div>
      <nav className={styles.nav}>
        {links
          .filter((link) => (state.status === "authenticated" ? can(link.perm) : false))
          .map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `${styles.navItem} ${isActive ? styles.active : ""}`}
            >
              {link.label}
            </NavLink>
          ))}
      </nav>
    </aside>
  );
}
