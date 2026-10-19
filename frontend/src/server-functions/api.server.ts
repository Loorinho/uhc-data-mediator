import { getRequest } from "@tanstack/react-start/server";
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getAppSession } from "./session.server";

const rawUrl = process.env.API_BASE_URL;

if (!rawUrl) {
	throw new Error(
		"API_BASE_URL is not set. The frontend server cannot reach the API without it.",
	);
}

// Normalize so endpoint paths can be joined consistently.
const url = rawUrl.endsWith("/") ? rawUrl : `${rawUrl}/`;

const api = axios.create({
	baseURL: url,
	headers: {
		"Content-Type": "application/json",
	},
	timeout: 20000, // timeout after 20 seconds
});

const publicRoutes = [
	"auth/login",
	"auth/refresh",
];

const isPublicRoute = (url?: string) => {
	if (!url) return false;

	return publicRoutes.some((route) => url.startsWith(route));
};

let refreshPromise: Promise<string> | null = null;

/**
 * Refreshes the access token.
 * If another request is already refreshing, wait for it instead.
 */
async function refreshAccessToken(): Promise<string> {
	if (refreshPromise) {
		return refreshPromise;
	}

	refreshPromise = (async () => {
		const { user } = await getAppSession();

		if (!user?.token || !user?.refreshToken) {
			throw new Error("No refresh token available.");
		}

		const refreshResponse = await axios.post(
			`${url}auth/refresh/`,
			{
				refresh: user.refreshToken,
			},
			{
				headers: {
					"Content-Type": "application/json",
				},
			},
		);

		const response = refreshResponse.data as {
			statusCode: number;
			message: string;
			data: {
                tokens: {
                    access: string;
                    refresh: string;
                }
			};
		};


		const userSession = await getAppSession();

		userSession.user = {
			...user,
			token: response.data.tokens.access,
			refreshToken: response.data.tokens.refresh,
		};

		await userSession.save();

		return response.data.tokens.access;
	})();

	try {
		return await refreshPromise;
	} finally {
		refreshPromise = null;
	}
}

api.interceptors.request.use(async (config) => {
	const request = getRequest();
	config.headers["X-Original-User-Agent"] =
		request.headers.get("user-agent") ?? "";

	if (isPublicRoute(config.url)) {
		return config;
	}

	const session = await getAppSession();
	const token = session.user?.token;

	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}

	return config;
});

api.interceptors.response.use(
	(response) => response,
	async (error: AxiosError) => {
		const originalRequest = error.config as InternalAxiosRequestConfig & {
			_retry?: boolean;
		};

		if (
			error.response?.status !== 401 ||
			originalRequest._retry ||
			isPublicRoute(originalRequest.url)
		) {
			return Promise.reject(error);
		}

		originalRequest._retry = true;

		try {
			const newToken = await refreshAccessToken();

			originalRequest.headers.Authorization = `Bearer ${newToken}`;

			return api(originalRequest);
		} catch (refreshError) {
			return Promise.reject(refreshError);
		}
	},
);

export default api;
