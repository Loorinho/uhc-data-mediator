import {
	createFileRoute,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import { ActiveBadge } from "@/components/status-badges";
import { Button } from "@/components/ui/button";
import { toDataTablePagination } from "@/lib/pagination";
import {
	getCanonicalMeasuresFn,
	measureSearchSchema,
} from "@/server-functions/canonical.api";
import type { CanonicalMeasure } from "@/types/types";

export const Route = createFileRoute(
	"/_authed/dashboard/explorer/canonical/measures",
)({
	validateSearch: (search) => measureSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getCanonicalMeasuresFn({ data: deps }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Canonical measures · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const columns: ColumnDef<typeof features, CanonicalMeasure>[] = [
	{ accessorKey: "code", header: "Code" },
	{ accessorKey: "name", header: "Name" },
	{ accessorKey: "unit", header: "Unit" },
	{ accessorKey: "aggregation_method", header: "Aggregation" },
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
			<div>
				<h1 className="text-2xl font-semibold">Canonical measures</h1>
				<p className="text-sm text-muted-foreground">
					Governed measure definitions shared across data products
				</p>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Status
					<select
						className="min-w-40 rounded-md border bg-background px-3 py-2"
						value={search.active ?? ""}
						disabled={isLoading}
						onChange={(event) =>
							updateSearch({
								active: (event.target.value || undefined) as
									| "true"
									| "false"
									| undefined,
								page: 1,
							})
						}
					>
						<option value="">All</option>
						<option value="true">Active</option>
						<option value="false">Inactive</option>
					</select>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() => updateSearch({ page: 1, active: undefined })}
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
				emptyMessage="No canonical measures found."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(measure) => measure.code}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
			/>
		</div>
	);
}
