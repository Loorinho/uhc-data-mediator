import type { AuthUser } from "@/server-functions/session.server";

type NavigationUser = Pick<AuthUser, "roles">;

export function isAdmin(user: Pick<AuthUser, "roles"> | null | undefined) {
	const roles = user?.roles || [];
	return roles.includes("admin");
}

export function isDataProvider(
	user: Pick<AuthUser, "roles"> | null | undefined,
) {
	const roles = user?.roles || [];
	return roles.includes("data_provider");
}

const navigationItems = {
	dashboard: { title: "Dashboard", url: "/dashboard" },
	users: { title: "Users", url: "/dashboard/users" },
	roles: { title: "Roles", url: "/dashboard/roles" },
	products: { title: "Products", url: "/dashboard/products" },
	acquisitions: { title: "Acquisitions", url: "/dashboard/acquisitions" },
} as const;

export type NavigationKey = keyof typeof navigationItems;

function getNavigationKeys(user: NavigationUser): NavigationKey[] {
	const keys = new Set<NavigationKey>();

	keys.add("dashboard");

	if (isAdmin(user)) {
		for (const key of ["users", "roles"] as const) {
			keys.add(key);
		}
	}

	if (isDataProvider(user)) {
		keys.add("acquisitions");
	}

	if (keys.size === 0) {
		keys.add("products");
	}

	return Array.from(keys);
}

export function getNavigationItems(user: NavigationUser) {
	return getNavigationKeys(user).map((key) => ({
		key,
		...navigationItems[key],
	}));
}

export function getDefaultRoute(user: NavigationUser) {
	return navigationItems[getNavigationKeys(user)[0]].url;
}

function isWithinRoute(pathname: string, route: string) {
	return pathname === route || pathname.startsWith(`${route}/`);
}
