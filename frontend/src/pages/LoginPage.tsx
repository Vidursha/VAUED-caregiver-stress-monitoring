import { useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Hospital } from "lucide-react";
import { useAuth } from "../auth/AuthContext";
import styles from "../styles/Login.module.css";

const LOGIN_ILLUSTRATION_SRC =
  "/login-hero-nurse.png";
const POST_LOGIN_SPLASH_KEY = "care_sync_post_login_splash";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, state } = useAuth();

  if (state.status === "authenticated") {
    return <Navigate to="/" replace />;
  }

  const redirectTo = useMemo(() => {
    const from = (location.state as any)?.from;
    return typeof from === "string" && from.startsWith("/") ? from : "/";
  }, [location.state]);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    const em = email.trim();
    if (!em || !password) {
      setError("Please enter your email/username and password.");
      return;
    }
    try {
      setLoading(true);
      await login({ email: em, password, remember });
      sessionStorage.setItem(POST_LOGIN_SPLASH_KEY, "1");
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError((err as Error).message || "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  const disabled = loading || state.status === "loading";

  return (
    <div className={styles.page}>
      <div className={styles.backgroundDecor} aria-hidden="true" />

      <main className={styles.showcase}>
        <section className={styles.heroPane}>
          <div className={styles.brandRow}>
            <div className={styles.brandIcon}>
              <Hospital size={18} />
            </div>
            <div>
              <h1>Care-Sync</h1>
              <p>Ward stress intelligence · secure access</p>
            </div>
          </div>

          <div className={styles.heroCard}>
            <h2>Welcome back</h2>
            <p>Sign in to continue to caregiver stress monitoring and ward insights.</p>
            <div className={styles.artWrap} aria-hidden="true">
              <div className={styles.artCircle} />
              <img
                src={LOGIN_ILLUSTRATION_SRC}
                alt="Healthcare nurse illustration"
                className={styles.heroImage}
              />
            </div>
          </div>
        </section>

        <section className={styles.card} aria-label="Sign in form">
          <div className={styles.cardHeader}>
            <h3>Sign in</h3>
            <p>LOGO Hospital · Primary role example: Ward Manager</p>
          </div>

          <form onSubmit={onSubmit} className={styles.form}>
            <label className={styles.label}>
              Email / Username
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="wardmanager@hospital.com"
                autoComplete="username"
                disabled={disabled}
              />
            </label>

            <label className={styles.label}>
              Password
              <div className={styles.passwordRow}>
                <input
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  disabled={disabled}
                />
                <button
                  type="button"
                  className={styles.iconButton}
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  disabled={disabled}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>

            <div className={styles.row}>
              <label className={styles.checkbox}>
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  disabled={disabled}
                />
                Remember me
              </label>
              <Link className={styles.link} to="/login" onClick={(e) => e.preventDefault()}>
                Forgot password?
              </Link>
            </div>

            {error ? <div className={styles.error}>{error}</div> : null}

            <button className={styles.primary} type="submit" disabled={disabled}>
              {loading ? "Signing in…" : "Sign in"}
            </button>

            <div className={styles.hint}>
              Use mock accounts like <strong>wardmanager@hospital.com</strong> / <strong>ward123</strong>.
            </div>
          </form>
        </section>
      </main>
    </div>
  );
}

