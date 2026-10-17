import { Link } from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";
import type { AcquisitionAttempt, AcquisitionStatus } from "@/types/types";

const statusVariant = {
	PENDING: "outline",
	RUNNING: "secondary",
	SUCCEEDED: "default",
	PARTIAL: "outline",
	FAILED: "destructive",
} as const;

export function AcquisitionStatusBadge({
	status,
}: {
	status: AcquisitionStatus;
}) {
	return <Badge variant={statusVariant[status]}>{status}</Badge>;
}

const features = tableFeatures({});

export const acquisitionColumns: ColumnDef<
	typeof features,
	AcquisitionAttempt
>[] = [
	{
		accessorKey: "acquisitionId",
		header: "Acquisition",
		cell: ({ row }) => (
			<Link
				className="font-mono text-xs underline underline-offset-4"
				to="/dashboard/acquisitions/$acquisitionId"
				params={{ acquisitionId: row.original.acquisitionId }}
				search={{ page: 1, page_size: 20, include_raw: false }}
			>
				{row.original.acquisitionId}
			</Link>
		),
	},
	{
		accessorKey: "mode",
		header: "Mode",
		cell: ({ row }) => <Badge variant="secondary">{row.original.mode}</Badge>,
	},
	{
		accessorKey: "status",
		header: "Status",
		cell: ({ row }) => <AcquisitionStatusBadge status={row.original.status} />,
	},
	{
		accessorKey: "outcome",
		header: "Outcome",
		cell: ({ row }) => row.original.outcome ?? "—",
	},
	{ accessorKey: "source", header: "Source" },
	{
		accessorKey: "requestedAt",
		header: "Requested",
		cell: ({ row }) => formatDateTime(row.original.requestedAt),
	},
	{
		accessorKey: "finishedAt",
		header: "Finished",
		cell: ({ row }) => formatDateTime(row.original.finishedAt),
	},
	{
		accessorKey: "durationMs",
		header: "Duration",
		cell: ({ row }) =>
			row.original.durationMs === null
				? "—"
				: `${row.original.durationMs.toLocaleString()} ms`,
	},
	{
		accessorKey: "recordsSaved",
		header: "Saved / received",
		cell: ({ row }) =>
			`${row.original.recordsSaved} / ${row.original.recordsReceived}`,
	},
	{
		accessorKey: "receivedCombinations",
		header: "Coverage",
		cell: ({ row }) =>
			`${row.original.receivedCombinations} / ${row.original.expectedCombinations}`,
	},
];
