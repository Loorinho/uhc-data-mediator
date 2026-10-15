"use client";

import {
	type ColumnDef,
	type RowData,
	tableFeatures,
	useTable,
} from "@tanstack/react-table";

import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from "@/components/ui/table";

// No optional features yet — the core row model is included automatically.
const features = tableFeatures({});
type Features = typeof features;

interface DataTableProps<TData extends RowData> {
	columns: ColumnDef<Features, TData>[];
	data: TData[];
	/** Message shown when there are no rows. */
	emptyMessage?: string;
}

export function DataTable<TData extends RowData>({
	columns,
	data,
	emptyMessage = "No results.",
}: DataTableProps<TData>) {
	const table = useTable({
		features,
		data,
		columns,
	});

	return (
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
							<TableRow key={row.id}>
								{row.getAllCells().map((cell) => (
									<TableCell key={cell.id}>
										<table.FlexRender cell={cell} />
									</TableCell>
								))}
							</TableRow>
						))
					) : (
						<TableRow>
							<TableCell colSpan={columns.length} className="h-24 text-center">
								{emptyMessage}
							</TableCell>
						</TableRow>
					)}
				</TableBody>
			</Table>
		</div>
	);
}
