import { createServerFn } from "@tanstack/react-start";
import axios from "axios";
import { z } from "zod";

import type {
	CanonicalObservation,
	DataProduct,
	DataProductRelease,
	ExplorationPage,
	PopulationTransformationResult,
	ReleaseLineage,
	TypedApiResponse,
} from "@/types/types";
import api from "./api.server";
import { getExplorationData } from "./exploration.server";

const paginationSchema = {
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
};

// -- Data products ------------------------------------------------------------

export const productSearchSchema = z.object(paginationSchema);

export const getDataProductsFn = createServerFn({ method: "GET" })
	.validator(productSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<DataProduct>>("data-products/", data),
	);

export const getDataProductDetailFn = createServerFn({ method: "GET" })
	.validator(z.object({ code: z.string().min(1) }))
	.handler(({ data }) =>
		getExplorationData<DataProduct>(`data-products/${data.code}/`),
	);

export const getProductReleasesFn = createServerFn({ method: "GET" })
	.validator(productSearchSchema.extend({ code: z.string().min(1) }))
	.handler(({ data: { code, ...params } }) =>
		getExplorationData<ExplorationPage<DataProductRelease>>(
			`data-products/${code}/releases/`,
			params,
		),
	);

// -- Releases -------------------------------------------------------------------

export const releaseSearchSchema = z.object({
	...paginationSchema,
	product_code: z.string().optional().catch(undefined),
	status: z
		.enum(["DRAFT", "VALIDATING", "READY", "PUBLISHED", "REJECTED"])
		.optional()
		.catch(undefined),
});

export const getReleasesFn = createServerFn({ method: "GET" })
	.validator(releaseSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<DataProductRelease>>(
			"data-product-releases/",
			data,
		),
	);

export const getReleaseDetailFn = createServerFn({ method: "GET" })
	.validator(z.object({ releaseId: z.uuid() }))
	.handler(({ data }) =>
		getExplorationData<DataProductRelease>(
			`data-product-releases/${data.releaseId}/`,
		),
	);

export const getReleaseObservationsFn = createServerFn({ method: "GET" })
	.validator(z.object({ ...paginationSchema, releaseId: z.uuid() }))
	.handler(({ data: { releaseId, ...params } }) =>
		getExplorationData<ExplorationPage<CanonicalObservation>>(
			`data-product-releases/${releaseId}/observations/`,
			params,
		),
	);

export const getReleaseLineageFn = createServerFn({ method: "GET" })
	.validator(z.object({ releaseId: z.uuid() }))
	.handler(({ data }) =>
		getExplorationData<ReleaseLineage>(
			`data-product-releases/${data.releaseId}/lineage/`,
		),
	);

// -- Population transformation ---------------------------------------------------

export const triggerPopulationTransformationFn = createServerFn({
	method: "POST",
})
	.validator(z.object({ code: z.literal("sl-district-population") }))
	.handler(async ({ data }) => {
		try {
			const response = await api.post<
				TypedApiResponse<PopulationTransformationResult>
			>(`data-products/${data.code}/transform/`, null, {
				validateStatus: () => true,
			});
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
