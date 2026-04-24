import type { Role } from "./types";

export type Permission =
  | "view:dashboard"
  | "view:caregivers"
  | "view:assistant"
  | "view:admin"
  | "manage:users"
  | "edit:settings";

const ROLE_PERMS: Record<Role, Permission[]> = {
  Admin: ["view:dashboard", "view:caregivers", "view:assistant", "view:admin", "manage:users", "edit:settings"],
  "Ward Manager": ["view:dashboard", "view:caregivers", "view:assistant", "edit:settings"],
  Doctor: ["view:dashboard", "view:caregivers", "view:assistant"],
  Nurse: ["view:dashboard", "view:caregivers", "view:assistant"],
  Viewer: ["view:dashboard", "view:caregivers", "view:assistant"],
};

export function permissionsFor(role: Role): Set<Permission> {
  return new Set(ROLE_PERMS[role] ?? []);
}

export function hasPermission(role: Role, perm: Permission) {
  return permissionsFor(role).has(perm);
}

export function isAdmin(role: Role) {
  return role === "Admin";
}

