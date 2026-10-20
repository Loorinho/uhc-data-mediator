import {
	createFileRoute,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";

import { DataTable } from "@/components/data-table";
import { PageError } from "@/components/page-error";
import { SensitivityBadge } from "@/components/status-badges";
import { Button } from "@/components/ui/button";
import { toDataTablePagination } from "@/lib/pagination";
import { formatDateTime } from "@/lib/utils";
import { getDataProductsFn, productSearchSchema } from "@/server-functions/products.api";
import type { DataProduct } from "@/types/types";

export const Route = createFileRoute("/_authed/dashboard/products/")({
	validateSearch: (search) => productSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getDataProductsFn({ data: deps }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Data products · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const columns: ColumnDef<typeof features, DataProduct>[] = [
	{
		accessorKey: "code",
		header: "Code",
		cell: ({ row }) => (
			<code className="text-xs">{row.original.code}</code>
		),
	},
	{ accessorKey: "title", header: "Title" },
	{ accessorKey: "source", header: "Source" },
	{
		accessorKey: "sensitivity_classification",
		header: "Sensitivity",
		cell: ({ row }) => (
			<SensitivityBadge sensitivity={row.original.sensitivity_classification} />
		),
	},
	{ accessorKey: "schema_version", header: "Schema" },
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
				<h1 className="text-2xl font-semibold">Data products</h1>
				<p className="text-sm text-muted-foreground">
					Governed data products you are authorized to view
				</p>
			</div>

			<div className="flex justify-end">
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
				emptyMessage="No data products are visible for your account."
				pagination={toDataTablePagination(pagination)}
				isLoading={isLoading}
				getRowId={(product) => product.id}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
				onRowClick={(product) =>
					void router.navigate({
						to: "/dashboard/products/$code",
						params: { code: product.code },
						search: { page: 1, page_size: 20 },
					})
				}
			/>
		</div>
	);
}
