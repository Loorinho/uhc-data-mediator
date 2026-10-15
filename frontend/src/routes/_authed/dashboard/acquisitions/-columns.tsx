import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";
import type { AcquisitionAttempt } from "@/types/types";

const statusVariant: Record<
	AcquisitionAttempt["status"],
	"default" | "secondary" | "destructive" | "outline"
> = {
	PENDING: "outline",
	RUNNING: "secondary",
	SUCCEEDED: "default",
	FAILED: "destructive",
};

// Same features object as the DataTable — keeps column typing in sync.
const features = tableFeatures({});

export const acquisitionColumns: ColumnDef<
	typeof features,
	AcquisitionAttempt
>[] = [
	{
		accessorKey: "id",
		header: "ID",
	},
	{
		accessorKey: "mode",
		header: "Mode",
		cell: ({row}) => <Badge variant="secondary">{row.original.mode}</Badge>,
	},
	{
		accessorKey: "status",
		header: "Status",
		cell: ({row}) => {
			const status = row.original.status	;
			return <Badge variant={statusVariant[status]}>{status}</Badge>;
		},
	},
	{
		accessorKey: "requestedBy",
		header: "Requested By",
	},
	{
		accessorKey: "requestedAt",
		header: "Requested At",
		cell: ({row}) => formatDateTime(row.original.requestedAt),
	},
	{
		accessorKey: "startedAt",
		header: "Started At",
		cell: ({row}) => formatDateTime(row.original.startedAt),
	},
	{
		accessorKey: "completedAt",
		header: "Completed At",
		cell: ({row}) => formatDateTime(row.original.completedAt),
	},
	{
		accessorKey: "errorMessage",
		header: "Error",
		cell: ({row}) => {
			const message = row.original.errorMessage;
			return message ? message : "-";
		},
	},
];
