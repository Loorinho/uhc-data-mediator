import {
	createFileRoute,
	Link,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import { Badge } from "@/components/ui/badge";
import { toDataTablePagination } from "@/lib/pagination";
import {
	acquisitionObservationsSearchSchema,
	getAcquisitionObservationsFn,
} from "@/server-functions/explorer.api";
import type { SourceObservation } from "@/types/types";

export const Route = createFileRoute(
	"/_authed/dashboard/acquisitions/$acquisitionId/observations",
)({
	validateSearch: (search) =>
		acquisitionObservationsSearchSchema
			.omit({ acquisitionId: true })
			.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ params, deps }) =>
		getAcquisitionObservationsFn({
			data: { acquisitionId: params.acquisitionId, ...deps },
		}),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Source observations · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const columns: ColumnDef<typeof features, SourceObservation>[] = [
	{
		accessorKey: "org_unit_name",
		header: "Organisation unit",
		cell: ({ row }) => row.original.org_unit_name || row.original.org_unit_id,
	},
	{
		accessorKey: "indicator_name",
		header: "Measure",
		cell: ({ row }) =>
			row.original.indicator_name || row.original.indicator_id,
	},
	{
		accessorKey: "measure_type",
		header: "Type",
		cell: ({ row }) => (
			<Badge variant="secondary">{row.original.measure_type}</Badge>
		),
	},
	{ accessorKey: "period", header: "Period" },
	{ accessorKey: "value", header: "Value" },
	{
		accessorKey: "dimensions",
		header: "Dimensions",
		cell: ({ row }) => (
			<code className="text-xs">{JSON.stringify(row.original.dimensions)}</code>
		),
	},
];

function RouteComponent() {
	const response = Route.useLoaderData();
	const { acquisitionId } = Route.useParams();
	const { items, pagination } = response.data;
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const isLoading = useRouterState({
		select: (state) => state.status === "pending",
	});
	const updateSearch = (changes: Partial<typeof search>) => {
		void navigate({
			search: (previous) => ({ ...previous, ...changes }),
			resetScroll: false,
		});
	};

	return (
		<div className="flex flex-col gap-4">
			<div className="space-y-2">
				<Link
					className="text-sm text-muted-foreground"
					to="/dashboard/acquisitions/$acquisitionId"
					params={{ acquisitionId }}
					search={{ page: 1, page_size: 20, include_raw: false }}
				>
					← Acquisition details
				</Link>
				<h1 className="text-2xl font-semibold">Source observations</h1>
				<p className="text-sm text-muted-foreground">
					Raw DHIS2 observations captured by this acquisition
				</p>
			</div>

			<DataTable
				columns={columns}
				data={items}
				emptyMessage="No observations were saved for this acquisition."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(item) => item.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
			/>
		</div>
	);
}
