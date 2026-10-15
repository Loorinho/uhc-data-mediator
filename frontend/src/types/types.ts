

export type ApiResponse = {
    statusCode: number;
    message: string;
}

export interface TypedApiResponse<T> extends ApiResponse {
    data: T;
}