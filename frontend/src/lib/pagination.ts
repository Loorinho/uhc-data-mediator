import type { ExplorationPagination, Pagination } from "@/types/types";

/**
 * Adapts the exploration endpoints' pagination envelope
 * ({ count, page, pageSize, totalPages, next, previous }) to the shape
 * consumed by the shared DataTable component.
 */
export function toDataTablePagination(
	pagination: ExplorationPagination,
): Pagination {
	return {
		page: pagination.page,
		pageSize: pagination.pageSize,
		totalItems: pagination.count,
		totalPages: pagination.totalPages,
		hasNext: pagination.next !== null,
		hasPrevious: pagination.previous !== null,
	};
}
