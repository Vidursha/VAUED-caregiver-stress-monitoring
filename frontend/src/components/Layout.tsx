import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { HeaderUserMenu } from "./HeaderUserMenu";
import styles from "../styles/Layout.module.css";

export function Layout() {
  return (
    <div className={styles.appShell}>
      <Sidebar />
      <main className={styles.content}>
        <header className={styles.topbar}>
          <div className={styles.topbarTitle}>
            <strong>Ward operations</strong>
            <span>Secure dashboard</span>
          </div>
          <HeaderUserMenu />
        </header>
        <Outlet />
      </main>
    </div>
  );
}
