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

// ---------------------------------------------------------------------------
// Exploration endpoints (districts, population, canonical, data products)
//
// These endpoints use the shared StandardPagination envelope, which differs
// slightly from the acquisition pagination envelope.
// ---------------------------------------------------------------------------

export type ExplorationPagination = {
	count: number;
	page: number;
	pageSize: number;
	totalPages: number;
	next: string | null;
	previous: string | null;
};

export type ExplorationPage<T> = {
	items: T[];
	pagination: ExplorationPagination;
};

// -- Districts -------------------------------------------------------------

export type DistrictMappingStatus = "MAPPED" | "UNMAPPED" | "AMBIGUOUS" | "IGNORED";

export type District = {
	id: string;
	name: string;
	code: string;
	dhis2_org_unit_id: string | null;
	dhis2_name: string | null;
	mapping_status: DistrictMappingStatus;
	mapping_notes: string;
	is_active: boolean;
};

// -- Population ------------------------------------------------------------

export type PopulationRecord = {
	id: string;
	district: District;
	reference_year: number;
	population: number;
	source: string;
	source_url: string;
	source_notes: string;
	created_at: string;
};

// -- Source observations (per acquisition) ----------------------------------

export type SourceObservation = {
	id: string;
	indicator_id: string;
	indicator_name: string;
	measure_type: "DATA_ELEMENT" | "INDICATOR";
	org_unit_id: string;
	org_unit_name: string;
	district: string | null;
	period: string;
	value: string;
	dimensions: Record<string, JsonValue>;
	attempt: string;
	source: string;
	created_at: string;
};

// -- Canonical interoperability ---------------------------------------------

export type CanonicalMeasure = {
	code: string;
	name: string;
	description: string;
	unit: string;
	aggregation_method: string;
	definition: string;
	is_active: boolean;
};

export type MeasureSourceMapping = {
	id: string;
	source: string;
	source_measure_id: string;
	measure: CanonicalMeasure;
};

export type CanonicalObservation = {
	id: string;
	measure: CanonicalMeasure;
	district: { id: string; name: string };
	period: string;
	period_type: string;
	value: string;
	dimensions: Record<string, JsonValue>;
	schema_version: string;
	release: string;
	source_type: "DHIS2" | "CENSUS_POPULATION";
	source_observation: string | null;
	source_population: string | null;
	transformed_at: string;
};

// -- Governance: data products & releases -----------------------------------

export type DataProduct = {
	id: string;
	code: string;
	title: string;
	purpose: string;
	source: string;
	schema_version: string;
	sensitivity_classification: "PUBLIC" | "INTERNAL" | "RESTRICTED";
	permitted_evidence: JsonValue[];
	quality_policy: Record<string, JsonValue>;
	data_owner_id: number;
	created_at: string;
	updated_at: string;
};

export type ReleaseStatus =
	| "DRAFT"
	| "VALIDATING"
	| "READY"
	| "PUBLISHED"
	| "REJECTED";

export type TransformationStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export type QualityStatus = "NOT_CHECKED" | "PASSED" | "WARNING" | "FAILED";

export type DataProductRelease = {
	id: string;
	product: string;
	product_code: string;
	version: number;
	source_acquisition: string | null;
	schema_version: string;
	status: ReleaseStatus;
	transformation_status: TransformationStatus;
	quality_status: QualityStatus;
	geographic_coverage: Record<string, JsonValue>;
	temporal_coverage: Record<string, JsonValue>;
	refresh_date: string | null;
	quality_report: Record<string, JsonValue>;
	lineage: Record<string, JsonValue>;
	created_at: string;
	published_at: string | null;
	published_by: number | null;
	observation_count: number;
};

export type ReleaseLineage = {
	releaseId: string;
	productCode: string;
	version: number;
	sourceAcquisitionId: string | null;
	lineage: Record<string, JsonValue>;
	geographicCoverage: Record<string, JsonValue>;
	temporalCoverage: Record<string, JsonValue>;
};

export type PopulationTransformationResult = {
	releaseId: string;
	version: number;
	status: ReleaseStatus;
	transformationStatus: TransformationStatus;
	created: boolean;
};
