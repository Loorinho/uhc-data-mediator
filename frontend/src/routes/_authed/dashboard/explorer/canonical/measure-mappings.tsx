import {
	createFileRoute,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toDataTablePagination } from "@/lib/pagination";
import {
	getMeasureMappingsFn,
	measureMappingSearchSchema,
} from "@/server-functions/canonical.api";
import type { MeasureSourceMapping } from "@/types/types";

export const Route = createFileRoute(
	"/_authed/dashboard/explorer/canonical/measure-mappings",
)({
	validateSearch: (search) => measureMappingSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getMeasureMappingsFn({ data: deps }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Measure mappings · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const columns: ColumnDef<typeof features, MeasureSourceMapping>[] = [
	{ accessorKey: "source", header: "Source" },
	{
		accessorKey: "source_measure_id",
		header: "Source measure ID",
		cell: ({ row }) => (
			<code className="text-xs">{row.original.source_measure_id}</code>
		),
	},
	{
		accessorKey: "measure",
		header: "Canonical measure",
		cell: ({ row }) => row.original.measure.name,
	},
	{
		accessorKey: "measure_code",
		header: "Measure code",
		cell: ({ row }) => row.original.measure.code,
	},
];

function RouteComponent() {
	const response = Route.useLoaderData();
	const { items, pagination } = response.data;
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const router = useRouter();
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
			<div>
				<h1 className="text-2xl font-semibold">Measure mappings</h1>
				<p className="text-sm text-muted-foreground">
					How upstream source measures map onto canonical measures
				</p>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Source
					<Input
						className="min-w-56"
						placeholder="e.g. DHIS2-SL-DEMO"
						defaultValue={search.source ?? ""}
						disabled={isLoading}
						onKeyDown={(event) => {
							if (event.key === "Enter") {
								updateSearch({
									source: event.currentTarget.value || undefined,
									page: 1,
								});
							}
						}}
					/>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() => updateSearch({ page: 1, source: undefined })}
				>
					Clear filters
				</Button>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() => void router.invalidate()}
				>
					Refresh
				</Button>
			</div>

			<DataTable
				columns={columns}
				data={items}
				emptyMessage="No measure mappings found."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(mapping) => mapping.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
			/>
		</div>
	);
}
