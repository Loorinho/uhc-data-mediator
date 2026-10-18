import type { AuthUser } from "@/server-functions/session.server";

export type Role = "admin" | "data_provider" | "analyst";

type RoleUser = Pick<AuthUser, "roles"> | null | undefined;

export function hasRole(user: RoleUser, role: Role) {
	return (user?.roles ?? []).includes(role);
}

export function isAdmin(user: RoleUser) {
	return hasRole(user, "admin");
}

export function isDataProvider(user: RoleUser) {
	return hasRole(user, "data_provider");
}

export function isAnalyst(user: RoleUser) {
	return hasRole(user, "analyst");
}

/**
 * View acquisition history/details. The backend narrows non-staff users to
 * their own attempts, so any authenticated role may open the pages.
 */
export function canViewAcquisitions(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user) || isAnalyst(user);
}

/** Trigger a new acquisition (POST /acquisition/). */
export function canTriggerAcquisition(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user);
}

/** Districts & population exploration. */
export function canExploreSourceData(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user) || isAnalyst(user);
}

/** Canonical measures/mappings/observations. */
export function canViewCanonicalData(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user) || isAnalyst(user);
}

/** Data products, releases, observations, lineage. */
export function canViewDataProducts(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user) || isAnalyst(user);
}

/** Trigger ANC canonical transformation for an acquisition. */
export function canTriggerTransformation(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user);
}

/**
 * Trigger the population transformation. The backend restricts this to
 * staff and the product owner, so only admins and owning data providers
 * are allowed in the UI.
 */
export function canTriggerPopulationTransformation(user: RoleUser) {
	return isAdmin(user) || isDataProvider(user);
}

/** Administrative/governance-only areas (users, roles, …). */
export function canViewAdministration(user: RoleUser) {
	return isAdmin(user);
}

// NOTE: A dedicated "data_steward" role is planned post-MVP; for now admin
// covers steward responsibilities. Extend these helpers when it is added.
