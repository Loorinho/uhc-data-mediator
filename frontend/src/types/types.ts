export type ApiResponse = {
	statusCode: number;
	message: string;
};

export interface TypedApiResponse<T> extends ApiResponse {
	data: T;
}

export type AcquisitionMode = "LIVE" | "FIXTURE";

export type AcquisitionStatus =
	| "PENDING"
	| "RUNNING"
	| "SUCCEEDED"
	| "PARTIAL"
	| "FAILED";

export type AcquisitionOutcome = "OK" | "INCOMPLETE" | "ERROR" | "TIMEOUT";

export type Pagination = {
	page: number;
	pageSize: number;
	totalItems: number;
	totalPages: number;
	hasNext: boolean;
	hasPrevious: boolean;
};

export type PaginatedItems<T> = { items: T[]; pagination: Pagination };

export type JsonValue =
	| string
	| number
	| boolean
	| null
	| JsonValue[]
	| { [key: string]: JsonValue };

export type AcquisitionConfiguration = {
	dx_ids?: string[];
	periods?: string[];
	org_unit_ids?: string[];
};

export type AcquisitionAttempt = {
	acquisitionId: string;
	correlationId: string;
	mode: AcquisitionMode;
	status: AcquisitionStatus;
	outcome: AcquisitionOutcome | null;
	source: string;
	configuration: AcquisitionConfiguration;
	startedAt: string | null;
	finishedAt: string | null;
	requestedAt: string;
	durationMs: number | null;
	recordsReceived: number;
	recordsSaved: number;
	expectedCombinations: number;
	receivedCombinations: number;
};

export type AcquisitionList = PaginatedItems<AcquisitionAttempt> & {
	statuses: AcquisitionStatus[];
	modes: AcquisitionMode[];
};

export type AcquisitionObservation = {
	observationId: string;
	measureId: string;
	measureName: string;
	measureType: "DATA_ELEMENT" | "INDICATOR";
	orgUnitId: string;
	orgUnitName: string;
	districtId: string | null;
	period: string;
	value: string;
	dimensions: Record<string, JsonValue>;
};

export type AcquisitionDetail = AcquisitionAttempt & {
	errorMessage: string;
	missingCombinations: JsonValue[];
	httpStatusCode: number | null;
	apiUrl: string;
	requestPayload: JsonValue;
	responsePayload?: JsonValue;
	observations: PaginatedItems<AcquisitionObservation>;
};
