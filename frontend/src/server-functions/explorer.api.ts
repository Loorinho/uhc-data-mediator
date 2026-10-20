import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

import type {
	District,
	ExplorationPage,
	PopulationRecord,
	SourceObservation,
} from "@/types/types";
import { getExplorationData } from "./exploration.server";

const paginationSchema = {
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
};

// -- Districts ---------------------------------------------------------------

export const districtSearchSchema = z.object({
	...paginationSchema,
	search: z.string().optional().catch(undefined),
	mapping_status: z
		.enum(["MAPPED", "VERIFIED", "UNMAPPED", "AMBIGUOUS", "IGNORED"])
		.optional()
		.catch(undefined),
});

export const getDistrictsFn = createServerFn({ method: "GET" })
	.validator(districtSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<District>>("districts/", data),
	);

export const getDistrictDetailFn = createServerFn({ method: "GET" })
	.validator(z.object({ districtId: z.uuid() }))
	.handler(({ data }) =>
		getExplorationData<District>(`districts/${data.districtId}/`),
	);

// -- Population --------------------------------------------------------------

export const populationSearchSchema = z.object({
	...paginationSchema,
	year: z.coerce.number().int().optional().catch(undefined),
	district_id: z.uuid().optional().catch(undefined),
});

export const getPopulationFn = createServerFn({ method: "GET" })
	.validator(populationSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<PopulationRecord>>("population/", data),
	);

export const getPopulationDetailFn = createServerFn({ method: "GET" })
	.validator(z.object({ populationId: z.uuid() }))
	.handler(({ data }) =>
		getExplorationData<PopulationRecord>(`population/${data.populationId}/`),
	);

// -- Acquisition source observations ------------------------------------------

export const acquisitionObservationsSearchSchema = z.object({
	...paginationSchema,
	acquisitionId: z.uuid(),
});

export const getAcquisitionObservationsFn = createServerFn({ method: "GET" })
	.validator(acquisitionObservationsSearchSchema)
	.handler(({ data: { acquisitionId, ...params } }) =>
		getExplorationData<ExplorationPage<SourceObservation>>(
			`acquisition/${acquisitionId}/observations/`,
			params,
		),
	);
