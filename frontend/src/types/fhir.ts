import type { JsonValue } from "./types";

export type FHIRExport = {
	id: string;
	releaseId: string;
	status: "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";
	fhirVersion: string;
	mappingVersion: string;
	resourceCount: number;
	resourceSummary: Record<string, JsonValue>;
	bundleSha256: string;
	requestedAt: string;
	startedAt: string | null;
	finishedAt: string | null;
	errorMessage: string;
};

export type FHIRValidation = {
	id: string;
	fhirExportId: string;
	status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
	classification: "CONFORMANT" | "CONFORMANT_WITH_WARNINGS" | "NON_CONFORMANT" | "BLOCKED" | "" | null;
	validatorName: string;
	validatorVersion: string;
	fhirVersion: string;
	bundleSha256: string;
	validatorReturnCode: number | null;
	counts: Record<"fatal" | "error" | "warning" | "information", number>;
	requestedAt: string;
	startedAt: string | null;
	finishedAt: string | null;
	errorMessage: string;
};

export type FHIRIssue = {
	id: string;
	source: "HL7_VALIDATOR" | "APPLICATION";
	severity: "fatal" | "error" | "warning" | "information";
	code: string;
	diagnostics: string;
	expression: JsonValue;
	resourceType: string;
	resourceId: string;
};

export type FHIRDocument = { text: string; filename: string };