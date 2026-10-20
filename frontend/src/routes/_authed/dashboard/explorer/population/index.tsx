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
import { formatDateTime } from "@/lib/utils";
import { toDataTablePagination } from "@/lib/pagination";
import {
	getPopulationFn,
	populationSearchSchema,
} from "@/server-functions/explorer.api";
import type { PopulationRecord } from "@/types/types";

export const Route = createFileRoute("/_authed/dashboard/explorer/population/")(
	{
		validateSearch: (search) => populationSearchSchema.parse(search),
		loaderDeps: ({ search }) => search,
		loader: ({ deps }) => getPopulationFn({ data: deps }),
		errorComponent: PageError,
		component: RouteComponent,
		head: () => ({
			meta: [{ title: "Population · UHC Data Mediator" }],
		}),
	},
);

const features = tableFeatures({});

const columns: ColumnDef<typeof features, PopulationRecord>[] = [
	{
		accessorKey: "district",
		header: "District",
		cell: ({ row }) => row.original.district.name,
	},
	{ accessorKey: "reference_year", header: "Reference year" },
	{
		accessorKey: "population",
		header: "Population",
		cell: ({ row }) => row.original.population.toLocaleString(),
	},
	{ accessorKey: "source", header: "Source" },
	{
		accessorKey: "created_at",
		header: "Recorded",
		cell: ({ row }) => formatDateTime(row.original.created_at),
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
				<h1 className="text-2xl font-semibold">Population records</h1>
				<p className="text-sm text-muted-foreground">
					District population figures by reference year (2021 census)
				</p>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Reference year
					<Input
						className="min-w-36"
						type="number"
						placeholder="e.g. 2021"
						defaultValue={search.year ?? ""}
						disabled={isLoading}
						onKeyDown={(event) => {
							if (event.key === "Enter") {
								const value = event.currentTarget.value;
								updateSearch({
									year: value ? Number(value) : undefined,
									page: 1,
								});
							}
						}}
					/>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() => updateSearch({ page: 1, year: undefined })}
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
				emptyMessage="No population records match these filters."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(record) => record.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
				onRowClick={(record) =>
					void router.navigate({
						to: "/dashboard/explorer/population/$populationId",
						params: { populationId: record.id },
					})
				}
			/>
		</div>
	);
}
