"use client";

import {
	type ColumnDef,
	type RowData,
	tableFeatures,
	useTable,
} from "@tanstack/react-table";
import { Button } from "@/components/ui/button";
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";
import type { Pagination } from "@/types/types";

// No optional features yet — the core row model is included automatically.
const features = tableFeatures({});
type Features = typeof features;

interface DataTableProps<TData extends RowData> {
	columns: ColumnDef<Features, TData>[];
	data: TData[];
	/** Message shown when there are no rows. */
	emptyMessage?: string;
	/** Server-owned pagination; data contains only the current page. */
	pagination?: Pagination;
	onPageChange?: (page: number) => void;
	onPageSizeChange?: (pageSize: number) => void;
	onRowClick?: (record: TData) => void;
	getRowId?: (record: TData) => string;
	isLoading?: boolean;
}

export function DataTable<TData extends RowData>({
	columns,
	data,
	emptyMessage = "No results.",
	pagination,
	onPageChange,
	onPageSizeChange,
	onRowClick,
	getRowId,
	isLoading = false,
}: DataTableProps<TData>) {
	const table = useTable({
		features,
		data,
		columns,
	});

	return (
		<div className="space-y-3" aria-busy={isLoading}>
			<div className="overflow-hidden rounded-md border">
				<Table>
					<TableHeader>
						{table.getHeaderGroups().map((headerGroup) => (
							<TableRow key={headerGroup.id}>
								{headerGroup.headers.map((header) => (
									<TableHead key={header.id}>
										{header.isPlaceholder ? null : (
											<table.FlexRender header={header} />
										)}
									</TableHead>
								))}
							</TableRow>
						))}
					</TableHeader>
					<TableBody>
						{table.getRowModel().rows?.length ? (
							table.getRowModel().rows.map((row) => (
								<TableRow
									key={getRowId ? getRowId(row.original) : row.id}
									className={
										onRowClick
											? "cursor-pointer focus-visible:outline-2 focus-visible:outline-ring"
											: undefined
									}
									tabIndex={onRowClick ? 0 : undefined}
									onClick={
										onRowClick
											? (event) => {
													if (
														!(event.target as HTMLElement).closest(
															"a, button, input, select",
														)
													)
														onRowClick(row.original);
												}
											: undefined
									}
									onKeyDown={
										onRowClick
											? (event) => {
													if (
														event.target === event.currentTarget &&
														(event.key === "Enter" || event.key === " ")
													) {
														event.preventDefault();
														onRowClick(row.original);
													}
												}
											: undefined
									}
								>
									{row.getAllCells().map((cell) => (
										<TableCell key={cell.id}>
											<table.FlexRender cell={cell} />
										</TableCell>
									))}
								</TableRow>
							))
						) : (
							<TableRow>
								<TableCell
									colSpan={columns.length}
									className="h-24 text-center"
								>
									{emptyMessage}
								</TableCell>
							</TableRow>
						)}
					</TableBody>
				</Table>
			</div>
			{pagination && (
				<div className="flex flex-wrap items-center justify-between gap-3 text-sm">
					<p className="text-muted-foreground" aria-live="polite">
						{pagination.totalItems.toLocaleString()} records · Page{" "}
						{pagination.page} of {Math.max(1, pagination.totalPages)}
						{isLoading ? " · Loading…" : ""}
					</p>
					<div className="flex items-center gap-3">
						{onPageSizeChange && (
							<label className="flex items-center gap-2">
								Rows per page
								<select
									className="rounded-md border bg-background px-2 py-1.5"
									value={pagination.pageSize}
									disabled={isLoading}
									onChange={(event) =>
										onPageSizeChange(Number(event.target.value))
									}
								>
									{Array.from(
										new Set([10, 20, 25, 50, 100, pagination.pageSize]),
									)
										.sort((a, b) => a - b)
										.map((size) => (
											<option key={size} value={size}>
												{size}
											</option>
										))}
								</select>
							</label>
						)}
						<Button
							variant="outline"
							size="sm"
							disabled={isLoading || !pagination.hasPrevious || !onPageChange}
							onClick={() => onPageChange?.(pagination.page - 1)}
						>
							Previous
						</Button>
						<Button
							variant="outline"
							size="sm"
							disabled={isLoading || !pagination.hasNext || !onPageChange}
							onClick={() => onPageChange?.(pagination.page + 1)}
						>
							Next
						</Button>
					</div>
				</div>
			)}
		</div>
	);
}
