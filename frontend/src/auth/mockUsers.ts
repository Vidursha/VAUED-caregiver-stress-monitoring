import type { StoredUser } from "./types";

export const DEFAULT_MOCK_USERS: StoredUser[] = [
  {
    id: "u_admin",
    name: "Hospital Admin",
    email: "admin@hospital.com",
    password: "admin123",
    role: "Admin",
    active: true,
  },
  {
    id: "u_ward_mgr",
    name: "Ward Manager",
    email: "wardmanager@hospital.com",
    password: "ward123",
    role: "Ward Manager",
    active: true,
  },
  {
    id: "u_doctor",
    name: "Doctor",
    email: "doctor@hospital.com",
    password: "doctor123",
    role: "Doctor",
    active: true,
  },
  {
    id: "u_nurse",
    name: "Nurse",
    email: "nurse@hospital.com",
    password: "nurse123",
    role: "Nurse",
    active: true,
  },
  {
    id: "u_viewer",
    name: "Viewer",
    email: "viewer@hospital.com",
    password: "viewer123",
    role: "Viewer",
    active: true,
  },
];

