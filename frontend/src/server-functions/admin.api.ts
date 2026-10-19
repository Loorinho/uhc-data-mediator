import { createServerFn } from "@tanstack/react-start";
import { redirect } from "@tanstack/react-router";
import axios from "axios";
import { z } from "zod";
import { canViewAdministration } from "@/lib/permissions";
import type { TypedApiResponse } from "@/types/types";
import api from "./api.server";
import { getCurrentUser } from "./auth.api";

export type ManagedUser = { id: number; username: string; roles: string[] };
export type ManagedRole = { id: number; name: string };

export const registerUserSchema = z.object({
	username: z.string().trim().min(1, "Username is required.").max(150)
		.regex(/^[\w.@+-]+$/, "Use letters, numbers, and @/./+/-/_ only."),
	password: z.string().min(8, "Password must contain at least 8 characters."),
	role: z.string().min(1, "Select a role."),
});
export const createRoleSchema = z.object({
	name: z.string().trim().min(1, "Role name is required.").max(150),
});

export async function requireAdmin() {
	const { user } = await getCurrentUser();
	if (!canViewAdministration(user)) {
		throw redirect({ to: "/dashboard" });
	}
}

async function adminRequest<T>(path: string, data?: object): Promise<T> {
	await requireAdmin();
	try {
		const response = data
			? await api.post<TypedApiResponse<T>>(path, data)
			: await api.get<TypedApiResponse<T>>(path);
		if (response.data.statusCode !== 200 || response.data.data == null) {
			throw new Error(response.data.message || "The request could not be completed.");
		}
		return response.data.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			throw new Error(error.response?.data?.message ?? "Unable to reach the API. Please try again.");
		}
		throw error;
	}
}

export const getUsersFn = createServerFn({ method: "GET" })
	.handler(() => adminRequest<ManagedUser[]>("users/"));
export const getRolesFn = createServerFn({ method: "GET" })
	.handler(() => adminRequest<ManagedRole[]>("roles/"));
export const registerUserFn = createServerFn({ method: "POST" })
	.validator(registerUserSchema)
	.handler(({ data }) => adminRequest<{ username: string; roles: string[] }>("auth/register/", data));
export const createRoleFn = createServerFn({ method: "POST" })
	.validator(createRoleSchema)
	.handler(({ data }) => adminRequest<ManagedRole>("roles/", data));