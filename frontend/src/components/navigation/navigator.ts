import type { AuthUser } from "@/server-functions/session.server";
import { isAdmin, isDataProvider } from "@/lib/permissions";

export { isAdmin, isDataProvider };

type NavigationUser = Pick<AuthUser, "roles" | "is_superuser">;

const navigationItems = {
	dashboard: { title: "Dashboard", url: "/dashboard" },
	users: { title: "Users", url: "/dashboard/users" },
	roles: { title: "Roles", url: "/dashboard/roles" },
	products: { title: "Products", url: "/dashboard/products" },
	acquisitions: { title: "Acquisitions", url: "/dashboard/acquisitions" },
	districts: { title: "Districts", url: "/dashboard/explorer/districts" },
	population: { title: "Population", url: "/dashboard/explorer/population" },
	canonicalMeasures: {
		title: "Canonical measures",
		url: "/dashboard/explorer/canonical/measures",
	},
	measureMappings: {
		title: "Measure mappings",
		url: "/dashboard/explorer/canonical/measure-mappings",
	},
	canonicalObservations: {
		title: "Canonical observations",
		url: "/dashboard/explorer/canonical/observations",
	},
	releases: { title: "Releases", url: "/dashboard/products/releases" },
	fhir: { title: "FHIR bundles", url: "/dashboard/fhir" },
} as const;

export type NavigationKey = keyof typeof navigationItems;

function getNavigationKeys(user: NavigationUser): NavigationKey[] {
	const keys = new Set<NavigationKey>();


	if (isAdmin(user)) {
		for (const key of ["users", "roles"] as const) {
			keys.add(key);
		}
	}

	if (isDataProvider(user)) {
		keys.add("acquisitions");
	keys.add("dashboard");


	keys.add("districts");
	keys.add("population");

	keys.add("canonicalMeasures");
	keys.add("measureMappings");
	keys.add("canonicalObservations");
	keys.add("products");
	keys.add("releases");
	keys.add("fhir");
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

/** Prefer the deepest section, ignoring query parameters and trailing slashes. */
export function getActiveNavigationUrl(
	pathname: string,
	items: readonly { url: string }[],
) {
	const path = pathname.replace(/\/+$/, "") || "/";
	return items
		.filter(({ url }) => path === url || path.startsWith(`${url}/`))
		.sort((a, b) => b.url.length - a.url.length)[0]?.url;
}
