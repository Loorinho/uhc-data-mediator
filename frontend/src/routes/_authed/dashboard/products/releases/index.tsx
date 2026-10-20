import {
	createFileRoute,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import {
	QualityStatusBadge,
	ReleaseStatusBadge,
	TransformationStatusBadge,
} from "@/components/status-badges";
import { Button } from "@/components/ui/button";
import { toDataTablePagination } from "@/lib/pagination";
import { formatDateTime } from "@/lib/utils";
import { getReleasesFn, releaseSearchSchema } from "@/server-functions/products.api";
import type { DataProductRelease, ReleaseStatus } from "@/types/types";

export const Route = createFileRoute("/_authed/dashboard/products/releases/")({
	validateSearch: (search) => releaseSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getReleasesFn({ data: deps }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Releases · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const columns: ColumnDef<typeof features, DataProductRelease>[] = [
	{
		accessorKey: "product_code",
		header: "Product",
		cell: ({ row }) => (
			<code className="text-xs">{row.original.product_code}</code>
		),
	},
	{ accessorKey: "version", header: "Version" },
	{
		accessorKey: "status",
		header: "Status",
		cell: ({ row }) => <ReleaseStatusBadge status={row.original.status} />,
	},
	{
		accessorKey: "transformation_status",
		header: "Transformation",
		cell: ({ row }) => (
			<TransformationStatusBadge status={row.original.transformation_status} />
		),
	},
	{
		accessorKey: "quality_status",
		header: "Quality",
		cell: ({ row }) => (
			<QualityStatusBadge status={row.original.quality_status} />
		),
	},
	{
		accessorKey: "observation_count",
		header: "Observations",
		cell: ({ row }) => row.original.observation_count.toLocaleString(),
	},
	{
		accessorKey: "created_at",
		header: "Created",
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
				<h1 className="text-2xl font-semibold">Data product releases</h1>
				<p className="text-sm text-muted-foreground">
					All releases across the products you can view
				</p>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Status
					<select
						className="min-w-40 rounded-md border bg-background px-3 py-2"
						value={search.status ?? ""}
						disabled={isLoading}
						onChange={(event) =>
							updateSearch({
								status: (event.target.value || undefined) as
									| ReleaseStatus
									| undefined,
								page: 1,
							})
						}
					>
						<option value="">All statuses</option>
						{["DRAFT", "VALIDATING", "READY", "PUBLISHED", "REJECTED"].map(
							(value) => (
								<option key={value} value={value}>
									{value}
								</option>
							),
						)}
					</select>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() => updateSearch({ page: 1, status: undefined })}
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
				emptyMessage="No releases match these filters."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(release) => release.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
				onRowClick={(release) =>
					void router.navigate({
						to: "/dashboard/products/releases/$releaseId",
						params: { releaseId: release.id },
						search: { page: 1, page_size: 20 },
					})
				}
			/>
		</div>
	);
}
