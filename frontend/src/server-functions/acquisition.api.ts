import { createServerFn } from "@tanstack/react-start";
import axios from "axios";
import { z } from "zod";

import type {
	AcquisitionDetail,
	AcquisitionList,
	ApiResponse,
	TypedApiResponse,
} from "@/types/types";
import api from "./api.server";

const triggerAcquisitionSchema = z.object({
	mode: z.enum(["LIVE", "FIXTURE"]),
});

export const acquisitionSearchSchema = z.object({
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(10),
	status: z
		.enum(["PENDING", "RUNNING", "SUCCEEDED", "PARTIAL", "FAILED"])
		.optional()
		.catch(undefined),
	mode: z.enum(["LIVE", "FIXTURE"]).optional().catch(undefined),
});

export const acquisitionDetailSearchSchema = z.object({
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
	include_raw: z.preprocess(
		(value) => value === true || value === "true",
		z.boolean(),
	),
});

async function getAcquisitionData<T>(path: string, params: object) {
	try {
		const response = await api.get<TypedApiResponse<T>>(path, { params });
		if (response.data.statusCode !== 200 || !response.data.data) {
			throw new Error(
				response.data.message || "Could not retrieve acquisition data.",
			);
		}
		return response.data;
	} catch (error) {
		if (axios.isAxiosError(error)) {
			throw new Error(
				error.response?.data?.message ??
					error.response?.data?.detail ??
					"Unable to load acquisition data. Please try again.",
			);
		}
		throw error;
	}
}

export const getAcquisitionsFn = createServerFn({ method: "GET" })
	.validator(acquisitionSearchSchema)
	.handler(({ data }) =>
		getAcquisitionData<AcquisitionList>("acquisition/", data),
	);

export const getAcquisitionDetailFn = createServerFn({ method: "GET" })
	.validator(acquisitionDetailSearchSchema.extend({ acquisitionId: z.uuid() }))
	.handler(({ data: { acquisitionId, ...params } }) =>
		getAcquisitionData<AcquisitionDetail>(
			`acquisition/${acquisitionId}/`,
			params,
		),
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
