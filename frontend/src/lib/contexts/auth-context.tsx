import type { AuthUser } from "@/server-functions/session.server";
import { createContext } from "react";

export type AuthContextValue = {
	user: AuthUser | null;
	isLoading: boolean;
	refresh: () => Promise<void>;
	logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | undefined>(
	undefined,
);
