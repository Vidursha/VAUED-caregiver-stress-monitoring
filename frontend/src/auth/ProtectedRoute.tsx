import { useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { AppLoadingScreen } from "../components/AppLoadingScreen";

const POST_LOGIN_SPLASH_KEY = "care_sync_post_login_splash";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { state } = useAuth();
  const location = useLocation();
  const [showSplash, setShowSplash] = useState(false);

  useEffect(() => {
    if (state.status !== "authenticated") return;
    const shouldSplash = sessionStorage.getItem(POST_LOGIN_SPLASH_KEY) === "1";
    if (!shouldSplash) return;
    setShowSplash(true);
    const t = window.setTimeout(() => {
      sessionStorage.removeItem(POST_LOGIN_SPLASH_KEY);
      setShowSplash(false);
    }, 2000);
    return () => window.clearTimeout(t);
  }, [state.status]);

  if (state.status === "loading") return null;
  if (state.status !== "authenticated") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (showSplash) return <AppLoadingScreen />;
  return children;
}

