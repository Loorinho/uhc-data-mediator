export type ApiResponse = {
	statusCode: number;
	message: string;
};

export interface TypedApiResponse<T> extends ApiResponse {
	data: T;
}

export type AcquisitionMode = "LIVE" | "FIXTURE";

export type AcquisitionStatus = "PENDING" | "RUNNING" | "SUCCEEDED" | "FAILED";

export type AcquisitionAttempt = {
	id: number;
	mode: AcquisitionMode;
	status: AcquisitionStatus;
	errorMessage: string;
	requestedBy: string;
	startedAt: string | null;
	completedAt: string | null;
	requestedAt: string;
};
