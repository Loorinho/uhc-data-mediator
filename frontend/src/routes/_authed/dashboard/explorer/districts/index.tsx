import {
	createFileRoute,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import { ActiveBadge, MappingStatusBadge } from "@/components/status-badges";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toDataTablePagination } from "@/lib/pagination";
import { districtSearchSchema, getDistrictsFn } from "@/server-functions/explorer.api";
import type { District, DistrictMappingStatus } from "@/types/types";

export const Route = createFileRoute("/_authed/dashboard/explorer/districts/")({
	validateSearch: (search) => districtSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getDistrictsFn({ data: deps }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Districts · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const columns: ColumnDef<typeof features, District>[] = [
	{ accessorKey: "name", header: "District" },
	{ accessorKey: "code", header: "Code" },
	{
		accessorKey: "dhis2_name",
		header: "DHIS2 org unit",
		cell: ({ row }) => row.original.dhis2_name ?? "—",
	},
	{
		accessorKey: "dhis2_org_unit_id",
		header: "DHIS2 ID",
		cell: ({ row }) => (
			<code className="text-xs">{row.original.dhis2_org_unit_id ?? "—"}</code>
		),
	},
	{
		accessorKey: "mapping_status",
		header: "Mapping",
		cell: ({ row }) => (
			<MappingStatusBadge status={row.original.mapping_status} />
		),
	},
	{
		accessorKey: "is_active",
		header: "Status",
		cell: ({ row }) => <ActiveBadge active={row.original.is_active} />,
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
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-2xl font-semibold">Districts</h1>
					<p className="text-sm text-muted-foreground">
						Sierra Leone districts and their DHIS2 organisation unit mapping
					</p>
				</div>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Search
					<Input
						className="min-w-56"
						placeholder="District name…"
						defaultValue={search.search ?? ""}
						disabled={isLoading}
						onKeyDown={(event) => {
							if (event.key === "Enter") {
								updateSearch({
									search: event.currentTarget.value || undefined,
									page: 1,
								});
							}
						}}
					/>
				</label>
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Mapping status
					<select
						className="min-w-40 rounded-md border bg-background px-3 py-2"
						value={search.mapping_status ?? ""}
						disabled={isLoading}
						onChange={(event) =>
							updateSearch({
								mapping_status: (event.target.value || undefined) as
									| DistrictMappingStatus
									| undefined,
								page: 1,
							})
						}
					>
						<option value="">All</option>
						{["MAPPED", "UNMAPPED", "AMBIGUOUS", "IGNORED"].map((value) => (
							<option key={value} value={value}>
								{value}
							</option>
						))}
					</select>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() =>
						updateSearch({ page: 1, search: undefined, mapping_status: undefined })
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
				columns={columns}
				data={items}
				emptyMessage="No districts match these filters."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(district) => district.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
				onRowClick={(district) =>
					void router.navigate({
						to: "/dashboard/explorer/districts/$districtId",
						params: { districtId: district.id },
					})
				}
			/>
		</div>
	);
}
