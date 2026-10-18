import {
	createFileRoute,
	Link,
	useRouter,
	useRouterState,
} from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import { useState } from "react";

import { DataTable } from "@/components/data-table";
import { Detail, JsonDetails } from "@/components/detail";
import { PageError } from "@/components/page-error";
import {
	QualityStatusBadge,
	ReleaseStatusBadge,
	SensitivityBadge,
	TransformationStatusBadge,
} from "@/components/status-badges";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "@/components/ui/toast";
import { useAuth } from "@/lib/auth";
import { toDataTablePagination } from "@/lib/pagination";
import { canTriggerPopulationTransformation } from "@/lib/permissions";
import { formatDateTime } from "@/lib/utils";
import {
	getDataProductDetailFn,
	getProductReleasesFn,
	productSearchSchema,
	triggerPopulationTransformationFn,
} from "@/server-functions/products.api";
import type { DataProductRelease } from "@/types/types";

export const Route = createFileRoute("/_authed/dashboard/products/$code")({
	validateSearch: (search) => productSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: async ({ params, deps }) => {
		const [product, releases] = await Promise.all([
			getDataProductDetailFn({ data: { code: params.code } }),
			getProductReleasesFn({ data: { code: params.code, ...deps } }),
		]);
		return { product, releases };
	},
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Data product · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const releaseColumns: ColumnDef<typeof features, DataProductRelease>[] = [
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
	{
		accessorKey: "published_at",
		header: "Published",
		cell: ({ row }) => formatDateTime(row.original.published_at),
	},
];

function RouteComponent() {
	const { product, releases } = Route.useLoaderData();
	const { data: productData } = product;
	const { items, pagination } = releases.data;
	const { code } = Route.useParams();
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const router = useRouter();
	const { user } = useAuth();
	const isLoading = useRouterState({
		select: (state) => state.status === "pending",
	});
	const updateSearch = (changes: Partial<typeof search>) => {
		void navigate({
			search: (previous) => ({ ...previous, ...changes }),
			resetScroll: false,
		});
	};

	const [isTransforming, setIsTransforming] = useState(false);
	const mayTransformPopulation =
		code === "sl-district-population" &&
		canTriggerPopulationTransformation(user);

	const triggerPopulationTransformation = async () => {
		setIsTransforming(true);
		try {
			const result = await triggerPopulationTransformationFn({
				data: { code: "sl-district-population" },
			});
			if (result.statusCode === 200) {
				toast.add({
					title: "Population transformation",
					description: result.message,
				});
				await router.invalidate();
			} else {
				toast.add({
					title: "Transformation failed",
					description:
						result.message ?? "The transformation could not be completed.",
				});
			}
		} catch (error) {
			toast.add({
				title: "Transformation failed",
				description:
					error instanceof Error
						? error.message
						: "An unexpected error occurred.",
			});
		} finally {
			setIsTransforming(false);
		}
	};

	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-wrap items-center justify-between gap-3">
				<div className="space-y-2">
					<Link
						className="text-sm text-muted-foreground"
						to="/dashboard/products"
						search={{ page: 1, page_size: 20 }}
					>
						← All data products
					</Link>
					<h1 className="text-2xl font-semibold text-primary">
						{productData.title}
					</h1>
					<p className="text-sm text-muted-foreground">{productData.code}</p>
				</div>
				{mayTransformPopulation && (
					<Button
						disabled={isTransforming}
						onClick={() => void triggerPopulationTransformation()}
					>
						{isTransforming ? (
							<>
								<Spinner data-icon="inline-start" />
								Transforming…
							</>
						) : (
							"Run population transformation"
						)}
					</Button>
				)}
			</div>

			<section className="space-y-5 rounded-xl border bg-card p-6">
				<div className="flex flex-wrap items-center gap-2">
					<SensitivityBadge
						sensitivity={productData.sensitivity_classification}
					/>
					<span className="text-xs text-muted-foreground">
						Schema {productData.schema_version}
					</span>
				</div>
				<p className="text-sm">{productData.purpose}</p>
				<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
					<Detail label="Source">{productData.source}</Detail>
					<Detail label="Created">
						{formatDateTime(productData.created_at)}
					</Detail>
					<Detail label="Updated">
						{formatDateTime(productData.updated_at)}
					</Detail>
				</dl>
				<div className="grid gap-4 lg:grid-cols-2">
					<div className="space-y-2">
						<h2 className="text-sm font-medium">Permitted evidence</h2>
						<JsonDetails value={productData.permitted_evidence} />
					</div>
					<div className="space-y-2">
						<h2 className="text-sm font-medium">Quality policy</h2>
						<JsonDetails value={productData.quality_policy} />
					</div>
				</div>
			</section>

			<section className="space-y-4">
				<h2 className="text-lg font-semibold">Releases</h2>
				<DataTable
					columns={releaseColumns}
					data={items}
					emptyMessage="This product has no releases yet."
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
			</section>
		</div>
	);
}
