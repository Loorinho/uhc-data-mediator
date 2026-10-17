import { loginSchema } from "@/routes";
import { createServerFn } from "@tanstack/react-start";
import api from "./api.server";
import type { TypedApiResponse } from "@/types/types";
import axios from "axios";
import { getAppSession } from "./session.server";
import { redirect } from "@tanstack/react-router";

type LoginResponse = {
    username: string,
    roles: string[];
    tokens: {
        access: string;
        refresh: string;
    }
}

export const getCurrentUser = createServerFn({ method: "GET" }).handler(
	async () => {
		const session = await getAppSession();
		return { user: session.user ?? null };
	},
);


export const loginFn = createServerFn({ method: "POST" })
	.validator(loginSchema)
	.handler(async ({ data }) => {
		try {
			const response = await api.post<TypedApiResponse<LoginResponse>>("auth/login/", data, {
				validateStatus: () => true,
			});

			if (
				response.data.statusCode === 200 &&
				response.data.data
			) {
				const session = await getAppSession();

				session.user = {
					username: response.data.data.username,
					roles: response.data.data.roles,
					refreshToken: response.data.data.tokens.refresh,
					token: response.data.data.tokens.access,
				};
				await session.save();
			}

			return response.data
		} catch (error) {
			if (axios.isAxiosError(error)) {
				// API unreachable
				if (!error.response) {
					throw new Error(
						"We are experiencing some technical difficulties. Please try again.",
					);
				}
				throw new Error(error.response?.data);
			}
		}
	});

	export const logoutFn = createServerFn({ method: "POST" }).handler(async () => {

	const session = await getAppSession();
	await session.destroy();
	
	throw redirect({
		to: "/",
	});
});
