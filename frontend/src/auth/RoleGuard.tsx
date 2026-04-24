import { Navigate } from "react-router-dom";
import type { Permission } from "./rbac";
import { useAuth } from "./AuthContext";

type Props = {
  require?: Permission;
  children: React.ReactNode;
  redirectTo?: string;
};

export function RoleGuard({ require, children, redirectTo = "/" }: Props) {
  const { can, state } = useAuth();
  if (state.status !== "authenticated") return <Navigate to="/login" replace />;
  if (require && !can(require)) return <Navigate to={redirectTo} replace />;
  return children;
}

