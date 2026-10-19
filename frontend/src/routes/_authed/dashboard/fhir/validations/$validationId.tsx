import { createFileRoute, Link, useRouterState } from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { Detail, JsonDetails } from "@/components/detail";
import { FHIRHeading, FHIRJobError, FHIRRefresh, FHIRStatus } from "@/components/fhir/shared";
import { PageError } from "@/components/page-error";
import { formatDateTime } from "@/lib/utils";
import { fhirIssueSearchSchema, getFHIRIssuesFn, getFHIRValidationFn } from "@/server-functions/fhir.api";
import type { FHIRIssue } from "@/types/fhir";

export const Route = createFileRoute("/_authed/dashboard/fhir/validations/$validationId")({
	validateSearch: (search) => fhirIssueSearchSchema.parse(search),
	loaderDeps: ({ search }) => search,
	loader: async ({ params, deps }) => {
		const [validation, issues] = await Promise.all([
			getFHIRValidationFn({ data: params }),
			getFHIRIssuesFn({ data: { ...params, ...deps } }),
		]);
		return { validation: validation.data, issues: issues.data };
	},
	errorComponent: PageError,
	head: () => ({ meta: [{ title: "FHIR validation · UHC Data Mediator" }] }),
	component: ValidationPage,
});

const features = tableFeatures({});
const columns: ColumnDef<typeof features, FHIRIssue>[] = [
	{ accessorKey: "severity", header: "Severity", cell: ({ row }) => <FHIRStatus value={row.original.severity} /> },
	{ accessorKey: "source", header: "Source" },
	{ accessorKey: "code", header: "Code" },
	{ accessorKey: "diagnostics", header: "Diagnostics", cell: ({ row }) => <div className="min-w-64 max-w-xl whitespace-pre-wrap break-words text-sm">{row.original.diagnostics || "—"}</div> },
	{ id: "resource", header: "Resource", cell: ({ row }) => <span className="break-all text-xs">{[row.original.resourceType, row.original.resourceId].filter(Boolean).join("/") || "—"}</span> },
	{ id: "expression", header: "Expression", cell: ({ row }) => <JsonDetails value={row.original.expression} /> },
];

function ValidationPage() {
	const { validation, issues } = Route.useLoaderData();
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const isLoading = useRouterState({ select: (state) => state.status === "pending" });
	const update = (changes: Partial<typeof search>) => { void navigate({ search: (previous) => ({ ...previous, ...changes }), resetScroll: false }); };
	return <div className="flex flex-col gap-6">
		<Link className="text-sm text-muted-foreground" to="/dashboard/fhir/exports/$exportId" params={{ exportId: validation.fhirExportId }} search={{ page: 1, page_size: 20 }}>← Export details</Link>
		<FHIRHeading title="FHIR validation" description={validation.id}>
			<FHIRRefresh active={["PENDING", "RUNNING"].includes(validation.status)} />
			{["COMPLETED", "FAILED"].includes(validation.status) && <Link className="rounded-md border bg-background px-4 py-2 text-sm font-medium hover:bg-muted" to="/dashboard/fhir/reports/$validationId" params={{ validationId: validation.id }}>View conformity report</Link>}
		</FHIRHeading>
		<FHIRJobError message={validation.errorMessage} />
		<section className="space-y-5 rounded-xl border bg-card p-6"><dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
			<Detail label="Job status"><FHIRStatus value={validation.status} /></Detail><Detail label="Conformity"><FHIRStatus value={validation.classification} /></Detail><Detail label="Validator">{validation.validatorName || "—"}</Detail><Detail label="Validator version">{validation.validatorVersion || "—"}</Detail>
			<Detail label="FHIR version">{validation.fhirVersion}</Detail><Detail label="Return code">{validation.validatorReturnCode ?? "—"}</Detail><Detail label="Requested">{formatDateTime(validation.requestedAt)}</Detail><Detail label="Started">{formatDateTime(validation.startedAt)}</Detail><Detail label="Finished">{formatDateTime(validation.finishedAt)}</Detail>
		</dl><Detail label="Validated bundle SHA-256"><span className="break-all font-mono text-xs">{validation.bundleSha256}</span></Detail></section>
		<div className="grid grid-cols-2 gap-4 lg:grid-cols-4">{Object.entries(validation.counts).map(([severity, count]) => <section key={severity} className="rounded-xl border bg-card p-4"><p className="text-sm capitalize text-muted-foreground">{severity}</p><p className="mt-2 text-2xl font-semibold">{count.toLocaleString()}</p></section>)}</div>
		<section className="space-y-4"><h2 className="text-lg font-semibold">Validation issues</h2><div className="flex flex-wrap gap-4">
			<label className="flex items-center gap-2 text-sm">Severity<select className="rounded-md border bg-background px-3 py-2" value={search.severity ?? ""} onChange={(event) => update({ severity: fhirIssueSearchSchema.shape.severity.parse(event.target.value || undefined), page: 1 })}><option value="">All severities</option>{["fatal", "error", "warning", "information"].map((severity) => <option key={severity} value={severity}>{severity}</option>)}</select></label>
			<label className="flex items-center gap-2 text-sm">Source<select className="rounded-md border bg-background px-3 py-2" value={search.source ?? ""} onChange={(event) => update({ source: fhirIssueSearchSchema.shape.source.parse(event.target.value || undefined), page: 1 })}><option value="">All sources</option><option value="HL7_VALIDATOR">HL7 Validator</option><option value="APPLICATION">Application</option></select></label>
		</div><DataTable columns={columns} data={issues.items} getRowId={(item) => item.id} pagination={issues.pagination} isLoading={isLoading} emptyMessage={["PENDING", "RUNNING"].includes(validation.status) ? "Validation is in progress; issues will appear when available." : "No issues match the selected filters. Check the final classification above for conformity."} onPageChange={(page) => update({ page })} onPageSizeChange={(page_size) => update({ page: 1, page_size })} /></section>
	</div>;
}