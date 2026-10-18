import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";

import type {
	CanonicalMeasure,
	CanonicalObservation,
	ExplorationPage,
	MeasureSourceMapping,
} from "@/types/types";
import { getExplorationData } from "./exploration.server";

const paginationSchema = {
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
};

// -- Canonical measures --------------------------------------------------------

export const measureSearchSchema = z.object({
	...paginationSchema,
	active: z
		.enum(["true", "false"])
		.optional()
		.catch(undefined),
});

export const getCanonicalMeasuresFn = createServerFn({ method: "GET" })
	.validator(measureSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<CanonicalMeasure>>(
			"interoperability/canonical/measures/",
			data,
		),
	);

// -- Measure mappings -----------------------------------------------------------

export const measureMappingSearchSchema = z.object({
	...paginationSchema,
	source: z.string().optional().catch(undefined),
});

export const getMeasureMappingsFn = createServerFn({ method: "GET" })
	.validator(measureMappingSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<MeasureSourceMapping>>(
			"interoperability/canonical/measure-mappings/",
			data,
		),
	);

// -- Canonical observations -------------------------------------------------------

export const canonicalObservationSearchSchema = z.object({
	...paginationSchema,
	release_id: z.uuid().optional().catch(undefined),
	measure: z.string().optional().catch(undefined),
	district_id: z.uuid().optional().catch(undefined),
	period: z.string().optional().catch(undefined),
});

export const getCanonicalObservationsFn = createServerFn({ method: "GET" })
	.validator(canonicalObservationSearchSchema)
	.handler(({ data }) =>
		getExplorationData<ExplorationPage<CanonicalObservation>>(
			"interoperability/canonical/observations/",
			data,
		),
	);

export const getCanonicalObservationDetailFn = createServerFn({ method: "GET" })
	.validator(z.object({ observationId: z.uuid() }))
	.handler(({ data }) =>
		getExplorationData<CanonicalObservation>(
			`interoperability/canonical/observations/${data.observationId}/`,
		),
	);
