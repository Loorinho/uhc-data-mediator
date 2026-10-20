import axios from "axios";
import type { TypedApiResponse } from "@/types/types";
import api from "./api.server";

/**
 * Shared fetch helper for the exploration-style endpoints (districts,
 * population, canonical, data products). Preserves backend error messages
 * and status codes.
 */
export async function getExplorationData<T>(path: string, params?: object) {
	try {
		const response = await api.get<TypedApiResponse<T>>(path, { params });
		if (response.data.statusCode !== 200 || response.data.data == null) {
			throw new Error(
				response.data.message || "Could not retrieve the requested data.",
			);
		}
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			if (!error.response) {
				throw new Error(
					"We are experiencing some technical difficulties. Please try again.",
				);
			}
			const body = error.response.data as
				| { message?: string; detail?: string }
				| undefined;
			throw new Error(
				body?.message ??
					body?.detail ??
					"Unable to load the requested data. Please try again.",
			);
		}
		throw error;
	}
}
