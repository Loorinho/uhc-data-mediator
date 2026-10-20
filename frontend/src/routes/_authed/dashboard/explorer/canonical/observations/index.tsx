import {
	createFileRoute,
	Link,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toDataTablePagination } from "@/lib/pagination";
import {
	canonicalObservationSearchSchema,
	getCanonicalObservationsFn,
} from "@/server-functions/canonical.api";
import type { CanonicalObservation } from "@/types/types";

export const Route = createFileRoute(
	"/_authed/dashboard/explorer/canonical/observations/",
)({
	validateSearch: (search) => canonicalObservationSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getCanonicalObservationsFn({ data: deps }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Canonical observations · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

export const canonicalObservationColumns: ColumnDef<
	typeof features,
	CanonicalObservation
>[] = [
	{
		accessorKey: "district",
		header: "District",
		cell: ({ row }) => row.original.district.name,
	},
	{
		accessorKey: "measure",
		header: "Measure",
		cell: ({ row }) => (
			<Link
				className="underline underline-offset-4"
				to="/dashboard/explorer/canonical/observations/$observationId"
				params={{ observationId: row.original.id }}
				aria-label={`View ${row.original.measure.name} for ${row.original.district.name}, ${row.original.period}`}
			>
				{row.original.measure.name}
			</Link>
		),
	},
	{ accessorKey: "period", header: "Period" },
	{ accessorKey: "period_type", header: "Period type" },
	{ accessorKey: "value", header: "Value" },
	{
		accessorKey: "source_type",
		header: "Source",
		cell: ({ row }) => (
			<Badge variant="secondary">{row.original.source_type}</Badge>
		),
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
				<h1 className="text-2xl font-semibold">Canonical observations</h1>
				<p className="text-sm text-muted-foreground">
					Transformed observations across all visible releases
				</p>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Measure code
					<Input
						className="min-w-44"
						placeholder="e.g. anc_first_visits"
						defaultValue={search.measure ?? ""}
						disabled={isLoading}
						onKeyDown={(event) => {
							if (event.key === "Enter") {
								updateSearch({
									measure: event.currentTarget.value || undefined,
									page: 1,
								});
							}
						}}
					/>
				</label>
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Period
					<Input
						className="min-w-32"
						placeholder="e.g. 2025"
						defaultValue={search.period ?? ""}
						disabled={isLoading}
						onKeyDown={(event) => {
							if (event.key === "Enter") {
								updateSearch({
									period: event.currentTarget.value || undefined,
									page: 1,
								});
							}
						}}
					/>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() =>
						updateSearch({ page: 1, measure: undefined, period: undefined })
					}
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
				columns={canonicalObservationColumns}
				data={items}
				emptyMessage="No canonical observations match these filters."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(item) => item.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
				onRowClick={(item) =>
					void router.navigate({
						to: "/dashboard/explorer/canonical/observations/$observationId",
						params: { observationId: item.id },
					})
				}
			/>
		</div>
	);
}
