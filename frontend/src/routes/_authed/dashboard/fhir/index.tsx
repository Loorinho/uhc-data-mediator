import { createFileRoute, Link, useRouterState } from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { FHIRHeading, FHIRRefresh, FHIRStatus } from "@/components/fhir/shared";
import { PageError } from "@/components/page-error";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";
import { fhirExportSearchSchema, getFHIRExportsFn } from "@/server-functions/fhir.api";
import type { FHIRExport } from "@/types/fhir";

export const Route = createFileRoute("/_authed/dashboard/fhir/")({
	validateSearch: (search) => fhirExportSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getFHIRExportsFn({ data: deps }),
	errorComponent: PageError,
	pendingComponent: () => <p role="status" className="p-6">Loading FHIR exports…</p>,
	head: () => ({ meta: [{ title: "FHIR bundles · UHC Data Mediator" }] }),
	component: FHIRExportsPage,
});

const features = tableFeatures({});
const columns: ColumnDef<typeof features, FHIRExport>[] = [
	{ accessorKey: "id", header: "Export", cell: ({ row }) => <Link className="font-mono text-xs underline underline-offset-4" to="/dashboard/fhir/exports/$exportId" params={{ exportId: row.original.id }} search={{ page: 1, page_size: 20 }}>{row.original.id}</Link> },
	{ accessorKey: "status", header: "Status", cell: ({ row }) => <FHIRStatus value={row.original.status} /> },
	{ accessorKey: "releaseId", header: "Release", cell: ({ row }) => <span className="font-mono text-xs">{row.original.releaseId}</span> },
	{ accessorKey: "resourceCount", header: "Resources" },
	{ accessorKey: "fhirVersion", header: "FHIR" },
	{ accessorKey: "requestedAt", header: "Requested", cell: ({ row }) => formatDateTime(row.original.requestedAt) },
];

function FHIRExportsPage() {
	const { items, pagination } = Route.useLoaderData().data;
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const isLoading = useRouterState({ select: (state) => state.status === "pending" });
	const update = (changes: Partial<typeof search>) => { void navigate({ search: (previous) => ({ ...previous, ...changes }), resetScroll: false }); };
	return <div className="flex flex-col gap-6">
		<FHIRHeading title="FHIR bundles" description="Explore generated bundles, validation history and conformity evidence."><FHIRRefresh active={items.some((item) => ["PENDING", "RUNNING"].includes(item.status))} /></FHIRHeading>
		<div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-card p-4">
			<p className="text-sm text-muted-foreground">Analysts can read bundles for published, public releases. Administrators and owning providers can generate exports from release details.</p>
			<Link className="text-sm font-medium text-primary underline" to="/dashboard/products/releases" search={{ page: 1, page_size: 20 }}>Browse releases</Link>
			{search.release_id && <div className="flex w-full items-center gap-3"><p className="break-all text-sm">Release: {search.release_id}</p><Button variant="outline" size="sm" onClick={() => update({ release_id: undefined, page: 1 })}>Clear filter</Button></div>}
		</div>
		<DataTable columns={columns} data={items} getRowId={(item) => item.id} pagination={pagination} isLoading={isLoading} emptyMessage="No FHIR exports are available in your access scope." onPageChange={(page) => update({ page })} onPageSizeChange={(page_size) => update({ page: 1, page_size })} />
	</div>;
}