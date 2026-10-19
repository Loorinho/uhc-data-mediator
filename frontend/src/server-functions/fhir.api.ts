import { createServerFn } from "@tanstack/react-start";
import axios from "axios";
import { z } from "zod";
import { isAdmin, isDataProvider } from "@/lib/permissions";
import type { FHIRDocument, FHIRExport, FHIRIssue, FHIRValidation } from "@/types/fhir";
import type { DataProduct, DataProductRelease, PaginatedItems, TypedApiResponse } from "@/types/types";
import api from "./api.server";
import { getCurrentUser } from "./auth.api";
import { getExplorationData } from "./exploration.server";

export const fhirPageSchema = z.object({
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
});
export const fhirExportSearchSchema = fhirPageSchema.extend({
	release_id: z.uuid().optional().catch(undefined),
});
export const fhirIssueSearchSchema = fhirPageSchema.extend({
	severity: z.enum(["fatal", "error", "warning", "information"]).optional().catch(undefined),
	source: z.enum(["HL7_VALIDATOR", "APPLICATION"]).optional().catch(undefined),
});
const exportIdSchema = z.object({ exportId: z.uuid() });
const validationIdSchema = z.object({ validationId: z.uuid() });
const releaseIdSchema = z.object({ releaseId: z.uuid() });

function requestError(error: unknown): never {
	if (axios.isAxiosError(error)) {
		throw new Error(error.response?.data?.message ?? "Unable to reach the FHIR API. Please try again.");
	}
	throw error;
}

async function queueJob<T>(path: string) {
	try {
		const response = await api.post<TypedApiResponse<T>>(path);
		if (response.data.statusCode !== 200 || !response.data.data) {
			throw new Error(response.data.message || "Unable to queue the FHIR job.");
		}
		return response.data;
	} catch (error) {
		return requestError(error);
	}
}

// Authorization remains enforced by Django on every request, including files.
// The additional check here decides whether owner-only controls should be shown.
export const getFHIRManagementAccessFn = createServerFn({ method: "GET" })
	.validator(releaseIdSchema)
	.handler(async ({ data }) => {
		const { user } = await getCurrentUser();
		if (isAdmin(user)) return true;
		if (!isDataProvider(user)) return false;
		try {
			const release = await getExplorationData<DataProductRelease>(`data-product-releases/${data.releaseId}/`);
			const [product, profile] = await Promise.all([
				getExplorationData<DataProduct>(`data-products/${release.data.product_code}/`),
				getExplorationData<{ id: number }>("auth/me/"),
			]);
			return product.data.data_owner_id === profile.data.id;
		} catch {
			// A provider may read a public bundle without owning its product.
			return false;
		}
	});

export const getFHIRExportsFn = createServerFn({ method: "GET" })
	.validator(fhirExportSearchSchema)
	.handler(({ data }) => getExplorationData<PaginatedItems<FHIRExport>>("fhir-exports/", data));

export const getFHIRExportFn = createServerFn({ method: "GET" })
	.validator(exportIdSchema)
	.handler(({ data }) => getExplorationData<FHIRExport>(`fhir-exports/${data.exportId}/`));

export const createFHIRExportFn = createServerFn({ method: "POST" })
	.validator(releaseIdSchema)
	.handler(({ data }) => queueJob<FHIRExport>(`data-product-releases/${data.releaseId}/fhir-exports/`));

export const getFHIRValidationsFn = createServerFn({ method: "GET" })
	.validator(fhirPageSchema.extend(exportIdSchema.shape))
	.handler(({ data: { exportId, ...params } }) =>
		getExplorationData<PaginatedItems<FHIRValidation>>(`fhir-exports/${exportId}/validations/`, params));

export const createFHIRValidationFn = createServerFn({ method: "POST" })
	.validator(exportIdSchema)
	.handler(({ data }) => queueJob<FHIRValidation>(`fhir-exports/${data.exportId}/validations/`));

export const getFHIRValidationFn = createServerFn({ method: "GET" })
	.validator(validationIdSchema)
	.handler(({ data }) => getExplorationData<FHIRValidation>(`fhir-validations/${data.validationId}/`));

export const getFHIRIssuesFn = createServerFn({ method: "GET" })
	.validator(fhirIssueSearchSchema.extend(validationIdSchema.shape))
	.handler(({ data: { validationId, ...params } }) =>
		getExplorationData<PaginatedItems<FHIRIssue>>(`fhir-validations/${validationId}/issues/`, params));

async function readDocument(path: string, filename: string): Promise<FHIRDocument> {
	try {
		const response = await api.get<string>(path, {
			responseType: "text",
			transformResponse: [(text: string) => text],
			validateStatus: () => true,
		});
		if (response.status !== 200) {
			let message = "The requested FHIR file is unavailable.";
			try { message = JSON.parse(response.data).message || message; } catch { /* Non-JSON gateway error. */ }
			throw new Error(message);
		}
		return { text: response.data, filename };
	} catch (error) {
		return requestError(error);
	}
}

export const getFHIRBundleFn = createServerFn({ method: "GET" })
	.validator(exportIdSchema)
	.handler(({ data }) => readDocument(`fhir-exports/${data.exportId}/bundle/`, `fhir_bundle_${data.exportId}.json`));

export const getFHIRReportFn = createServerFn({ method: "GET" })
	.validator(validationIdSchema)
	.handler(({ data }) => readDocument(`fhir-validations/${data.validationId}/report/`, `conformity_report_${data.validationId}.json`));