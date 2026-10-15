import { createServerFn } from "@tanstack/react-start";
import axios from "axios";
import { z } from "zod";

import type { AcquisitionAttempt, ApiResponse, TypedApiResponse } from "@/types/types";
import api from "./api.server";

const triggerAcquisitionSchema = z.object({
	mode: z.enum(["LIVE", "FIXTURE"]),
});

export const getAcquisitionsFn = createServerFn({ method: "GET" }).handler(
	async () => {
		const response = await api.get<TypedApiResponse<AcquisitionAttempt[]>>(
			"acquisition/",
			{ validateStatus: () => true },
		);
		return response.data;
	},
);

export const triggerAcquisitionFn = createServerFn({ method: "POST" })
	.validator(triggerAcquisitionSchema)
	.handler(async ({ data }) => {
		try {
			const response = await api.post<ApiResponse>(
				"acquisition/",
				{ mode: data.mode },
				{ validateStatus: () => true },
			);
			return response.data;
		} catch (error) {
			if (axios.isAxiosError(error) && !error.response) {
				throw new Error(
					"We are experiencing some technical difficulties. Please try again.",
				);
			}
			throw error;
		}
	});
