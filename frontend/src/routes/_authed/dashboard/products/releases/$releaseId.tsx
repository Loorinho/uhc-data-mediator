import { createFileRoute, Link, useRouter, useRouterState } from "@tanstack/react-router";
import { z } from "zod";

import { DataTable } from "@/components/data-table";
import { Detail, JsonDetails } from "@/components/detail";
import { FHIRAction } from "@/components/fhir/shared";
import { toast } from "@/components/ui/toast";
import { PageError } from "@/components/page-error";
import {
	QualityStatusBadge,
	ReleaseStatusBadge,
	TransformationStatusBadge,
} from "@/components/status-badges";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toDataTablePagination } from "@/lib/pagination";
import { formatDateTime } from "@/lib/utils";
import { canonicalObservationColumns } from "@/routes/_authed/dashboard/explorer/canonical/observations";
import { createFHIRExportFn, getFHIRManagementAccessFn } from "@/server-functions/fhir.api";
import {
	getReleaseDetailFn,
	getReleaseLineageFn,
	getReleaseObservationsFn,
} from "@/server-functions/products.api";

const releaseDetailSearchSchema = z.object({
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
});

export const Route = createFileRoute(
	"/_authed/dashboard/products/releases/$releaseId",
)({
	validateSearch: (search) => releaseDetailSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: async ({ params, deps }) => {
		const [release, observations, lineage, canManageFHIR] = await Promise.all([
			getReleaseDetailFn({ data: { releaseId: params.releaseId } }),
			getReleaseObservationsFn({ data: { releaseId: params.releaseId, ...deps } }),
			getReleaseLineageFn({ data: { releaseId: params.releaseId } }),
			getFHIRManagementAccessFn({ data: { releaseId: params.releaseId } }),
		]);
		return { release, observations, lineage, canManageFHIR };
	},
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Release details · UHC Data Mediator" }],
	}),
});

function RouteComponent() {
	const { release, observations, lineage, canManageFHIR } = Route.useLoaderData();
	const releaseData = release.data;
	const lineageData = lineage.data;
	const { items, pagination } = observations.data;
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
	const exportUnavailable = releaseData.product_code !== "sl-district-anc-activity"
		? "FHIR export currently supports only the ANC activity product."
		: releaseData.transformation_status !== "SUCCEEDED"
			? "Transformation must succeed before exporting."
			: releaseData.status === "REJECTED" || releaseData.quality_status === "FAILED"
				? "Rejected or quality-failed releases cannot be exported."
				: null;

	return (
		<div className="flex flex-col gap-6">
			<div className="space-y-2">
				<Link
					className="text-sm text-muted-foreground"
					to="/dashboard/products/$code"
					params={{ code: releaseData.product_code }}
					search={{ page: 1, page_size: 20 }}
				>
					← {releaseData.product_code}
				</Link>
				<h1 className="text-2xl font-semibold text-primary">
					{releaseData.product_code} · v{releaseData.version}
				</h1>
			</div>

			<section className="space-y-5 rounded-xl border bg-card p-6">
				<div className="flex flex-wrap items-center gap-2">
					<ReleaseStatusBadge status={releaseData.status} />
					<TransformationStatusBadge
						status={releaseData.transformation_status}
					/>
					<QualityStatusBadge status={releaseData.quality_status} />
					<span className="text-xs text-muted-foreground">
						Schema {releaseData.schema_version}
					</span>
				</div>
				<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
					<Detail label="Product">
						<Link
							className="underline underline-offset-4"
							to="/dashboard/products/$code"
							params={{ code: releaseData.product_code }}
							search={{ page: 1, page_size: 20 }}
						>
							{releaseData.product_code}
						</Link>
					</Detail>
					<Detail label="Version">{releaseData.version}</Detail>
					<Detail label="Created">
						{formatDateTime(releaseData.created_at)}
					</Detail>
					<Detail label="Refresh date">
						{formatDateTime(releaseData.refresh_date)}
					</Detail>
					<Detail label="Published">
						{formatDateTime(releaseData.published_at)}
					</Detail>
					<Detail label="Observations">
						{releaseData.observation_count.toLocaleString()}
					</Detail>
					<Detail label="Source acquisition">
						{releaseData.source_acquisition ? (
							<Link
								className="font-mono text-xs underline underline-offset-4"
								to="/dashboard/acquisitions/$acquisitionId"
								params={{ acquisitionId: releaseData.source_acquisition }}
								search={{ page: 1, page_size: 20, include_raw: false }}
							>
								{releaseData.source_acquisition}
							</Link>
						) : (
							"—"
						)}
					</Detail>
				</dl>
			</section>

			<section className="flex flex-wrap items-center justify-between gap-4 rounded-xl border bg-card p-5">
				<div className="space-y-1"><h2 className="font-semibold">FHIR interoperability</h2><p className="text-sm text-muted-foreground">Generate FHIR R4 bundles and inspect validation and conformity evidence.</p>{canManageFHIR && exportUnavailable && <p className="text-sm text-muted-foreground">{exportUnavailable}</p>}</div>
				<div className="flex flex-wrap items-center gap-3">
					<Link className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted" to="/dashboard/fhir" search={{ page: 1, page_size: 20, release_id: releaseData.id }}>View FHIR exports</Link>
					{canManageFHIR && <FHIRAction label="Export FHIR bundle" disabled={exportUnavailable !== null} action={async () => {
						const response = await createFHIRExportFn({ data: { releaseId: releaseData.id } });
						toast.add({ title: "FHIR generation queued", description: response.message });
						await router.navigate({ to: "/dashboard/fhir/exports/$exportId", params: { exportId: response.data.id }, search: { page: 1, page_size: 20 } });
					}} />}
				</div>
			</section>

			<Tabs defaultValue="observations">
				<TabsList>
					<TabsTrigger value="observations">Observations</TabsTrigger>
					<TabsTrigger value="lineage">Lineage &amp; coverage</TabsTrigger>
					<TabsTrigger value="quality">Quality report</TabsTrigger>
				</TabsList>
				<TabsContent value="observations" className="pt-4">
					<DataTable
						columns={canonicalObservationColumns}
						data={items}
						emptyMessage="This release has no observations."
						pagination={toDataTablePagination(pagination)}
						isLoading={isLoading}
						getRowId={(item) => item.id}
						onRowClick={(item) =>
							void router.navigate({
								to: "/dashboard/explorer/canonical/observations/$observationId",
								params: { observationId: item.id },
							})
						}
						onPageChange={(page) => updateSearch({ page })}
						onPageSizeChange={(page_size) =>
							updateSearch({ page: 1, page_size })
						}
					/>
				</TabsContent>
				<TabsContent value="lineage" className="pt-4">
					<section className="space-y-5 rounded-xl border bg-card p-6">
						<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
							<Detail label="Product">{lineageData.productCode}</Detail>
							<Detail label="Version">{lineageData.version}</Detail>
							<Detail label="Source acquisition">
								{lineageData.sourceAcquisitionId ?? "—"}
							</Detail>
						</dl>
						<div className="grid gap-4 lg:grid-cols-2">
							<div className="space-y-2">
								<h2 className="text-sm font-medium">Geographic coverage</h2>
								<JsonDetails value={lineageData.geographicCoverage} />
							</div>
							<div className="space-y-2">
								<h2 className="text-sm font-medium">Temporal coverage</h2>
								<JsonDetails value={lineageData.temporalCoverage} />
							</div>
						</div>
						<div className="space-y-2">
							<h2 className="text-sm font-medium">Lineage</h2>
							<JsonDetails value={lineageData.lineage} />
						</div>
					</section>
				</TabsContent>
				<TabsContent value="quality" className="pt-4">
					<section className="space-y-4 rounded-xl border bg-card p-6">
						<div className="flex items-center gap-2">
							<QualityStatusBadge status={releaseData.quality_status} />
						</div>
						<JsonDetails value={releaseData.quality_report} />
					</section>
				</TabsContent>
			</Tabs>
		</div>
	);
}
