import { useServerFn } from "@tanstack/react-start";
import { useEffect, useState } from "react";
import { AuthContext } from "../contexts/auth-context";
import type { AuthUser } from "@/server-functions/session.server";
import { getCurrentUser, logoutFn } from "@/server-functions/auth.api";

export function AuthProvider({ children }: { children: React.ReactNode }) {
	const loadCurrentUser = useServerFn(getCurrentUser);
	const runLogout = useServerFn(logoutFn);
	const [user, setUser] = useState<AuthUser | null>(null);
	const [isLoading, setIsLoading] = useState(true);

	async function refresh() {
		setIsLoading(true);

		try {
			const currentUser = await loadCurrentUser();
			setUser(currentUser.user ?? null);
		} finally {
			setIsLoading(false);
		}
	}

	async function logout() {
		await runLogout();
	}

	// biome-ignore lint/correctness/useExhaustiveDependencies: refresh is intentionally called once on mount
	useEffect(() => {
		void refresh();
	}, []);

	return (
		<AuthContext.Provider value={{ user, isLoading, refresh, logout }}>
			{children}
		</AuthContext.Provider>
	);
}
