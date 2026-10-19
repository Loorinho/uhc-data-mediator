import { createFileRoute, Link, useRouter, useRouterState } from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { Detail, JsonDetails } from "@/components/detail";
import { FHIRAction, FHIRHeading, FHIRJobError, FHIRRefresh, FHIRStatus } from "@/components/fhir/shared";
import { PageError } from "@/components/page-error";
import { toast } from "@/components/ui/toast";
import { formatDateTime } from "@/lib/utils";
import { createFHIRValidationFn, fhirPageSchema, getFHIRExportFn, getFHIRManagementAccessFn, getFHIRValidationsFn } from "@/server-functions/fhir.api";
import type { FHIRValidation } from "@/types/fhir";

export const Route = createFileRoute("/_authed/dashboard/fhir/exports/$exportId")({
	validateSearch: (search) => fhirPageSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: async ({ params, deps }) => {
		const [exportResponse, validations] = await Promise.all([
			getFHIRExportFn({ data: params }),
			getFHIRValidationsFn({ data: { ...params, ...deps } }),
		]);
		const canManage = await getFHIRManagementAccessFn({ data: { releaseId: exportResponse.data.releaseId } });
		return { exported: exportResponse.data, validations: validations.data, canManage };
	},
	errorComponent: PageError,
	head: () => ({ meta: [{ title: "FHIR export · UHC Data Mediator" }] }),
	component: ExportPage,
});

const features = tableFeatures({});
const columns: ColumnDef<typeof features, FHIRValidation>[] = [
	{ accessorKey: "id", header: "Validation", cell: ({ row }) => <Link className="font-mono text-xs underline" to="/dashboard/fhir/validations/$validationId" params={{ validationId: row.original.id }} search={{ page: 1, page_size: 20 }}>{row.original.id}</Link> },
	{ accessorKey: "status", header: "Status", cell: ({ row }) => <FHIRStatus value={row.original.status} /> },
	{ accessorKey: "classification", header: "Conformity", cell: ({ row }) => <FHIRStatus value={row.original.classification} /> },
	{ id: "errors", header: "Fatal / errors", cell: ({ row }) => `${row.original.counts.fatal} / ${row.original.counts.error}` },
	{ id: "warnings", header: "Warnings", cell: ({ row }) => row.original.counts.warning },
	{ accessorKey: "requestedAt", header: "Requested", cell: ({ row }) => formatDateTime(row.original.requestedAt) },
];

function ExportPage() {
	const { exported, validations, canManage } = Route.useLoaderData();
	const navigate = Route.useNavigate();
	const search = Route.useSearch();
	const router = useRouter();
	const isLoading = useRouterState({ select: (state) => state.status === "pending" });
	const busy = ["PENDING", "RUNNING"].includes(exported.status) || validations.items.some((validation) => ["PENDING", "RUNNING"].includes(validation.status));
	const update = (changes: Partial<typeof search>) => { void navigate({ search: (previous) => ({ ...previous, ...changes }), resetScroll: false }); };
	return <div className="flex flex-col gap-6">
		<Link className="text-sm text-muted-foreground" to="/dashboard/fhir" search={{ page: 1, page_size: 20, release_id: exported.releaseId }}>← Exports for this release</Link>
		<FHIRHeading title="FHIR export" description={exported.id}>
			<FHIRRefresh active={busy} />
			{exported.status === "SUCCEEDED" && <Link className="rounded-md border bg-background px-4 py-2 text-sm font-medium hover:bg-muted" to="/dashboard/fhir/bundles/$exportId" params={{ exportId: exported.id }}>View / download bundle</Link>}
			{canManage && <FHIRAction label="Run validation" disabled={exported.status !== "SUCCEEDED" || validations.items.some((validation) => ["PENDING", "RUNNING"].includes(validation.status))} action={async () => {
				const response = await createFHIRValidationFn({ data: { exportId: exported.id } });
				toast.add({ title: "Validation queued", description: response.message });
				await router.navigate({ to: "/dashboard/fhir/validations/$validationId", params: { validationId: response.data.id }, search: { page: 1, page_size: 20 } });
			}} />}
		</FHIRHeading>
		<FHIRJobError message={exported.errorMessage} />
		<section className="space-y-5 rounded-xl border bg-card p-6">
			<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
				<Detail label="Status"><FHIRStatus value={exported.status} /></Detail><Detail label="Resources">{exported.resourceCount.toLocaleString()}</Detail><Detail label="FHIR version">{exported.fhirVersion}</Detail><Detail label="Mapping version">{exported.mappingVersion}</Detail>
				<Detail label="Release">{exported.releaseId}</Detail><Detail label="Requested">{formatDateTime(exported.requestedAt)}</Detail><Detail label="Started">{formatDateTime(exported.startedAt)}</Detail><Detail label="Finished">{formatDateTime(exported.finishedAt)}</Detail>
			</dl><Detail label="Bundle SHA-256"><span className="break-all font-mono text-xs">{exported.bundleSha256 || "Not available yet"}</span></Detail>
			<div className="space-y-2"><h2 className="text-sm font-medium">Resource summary</h2><JsonDetails value={exported.resourceSummary} /></div>
		</section>
		<section className="space-y-4"><h2 className="text-lg font-semibold">Validation history</h2><DataTable columns={columns} data={validations.items} getRowId={(item) => item.id} pagination={validations.pagination} isLoading={isLoading} emptyMessage="No validations have been requested for this bundle." onPageChange={(page) => update({ page })} onPageSizeChange={(page_size) => update({ page: 1, page_size })} /></section>
	</div>;
}