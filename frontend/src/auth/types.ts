export type Role = "Admin" | "Ward Manager" | "Doctor" | "Nurse" | "Viewer";

export type AppUser = {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: boolean;
};

export type StoredUser = AppUser & {
  // Mock only (development). Do not use real passwords.
  password: string;
};

export type AuthSession = {
  user: AppUser;
  createdAt: number;
};

