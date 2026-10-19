import { createFileRoute, Link, redirect, useRouter, useRouterState } from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import { DataTable } from "@/components/data-table";
import { Detail, JsonDetails } from "@/components/detail";
import { PageError } from "@/components/page-error";
import { Button } from "@/components/ui/button";
import { canViewAuditEvents } from "@/lib/permissions";
import { formatDateTime } from "@/lib/utils";
import { type AuditSearch, auditSearchSchema, getAuditEventsFn } from "@/server-functions/audit.api";
import type { AuditEvent } from "@/types/audit";

export const Route = createFileRoute("/_authed/dashboard/audit/")({
	validateSearch: (search): AuditSearch => auditSearchSchema.parse(search),
	beforeLoad: ({ context }): void => {
		if (!canViewAuditEvents(context.user.user)) throw redirect({ to: "/dashboard" });
	},
	loaderDeps: ({ search }): AuditSearch => search,
	loader: ({ deps }) => getAuditEventsFn({ data: deps }),
	errorComponent: PageError,
	pendingComponent: () => <output className="block p-6">Loading audit events…</output>,
	head: () => ({ meta: [{ title: "Audit events · UHC Data Mediator" }] }),
	component: AuditEventsPage,
});

const features = tableFeatures({});
const columns: ColumnDef<typeof features, AuditEvent>[] = [
	{ accessorKey: "createdAt", header: "Time", cell: ({ row }) => formatDateTime(row.original.createdAt) },
	{ accessorKey: "action", header: "Action" },
	{ accessorKey: "outcome", header: "Outcome", cell: ({ row }) => <span className={`rounded-full px-2 py-1 text-xs font-medium ${row.original.outcome === "SUCCESS" ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400" : row.original.outcome === "DENIED" ? "bg-amber-500/10 text-amber-700 dark:text-amber-400" : "bg-red-500/10 text-red-700 dark:text-red-400"}`}>{row.original.outcome}</span> },
	{ accessorKey: "actorIdentifier", header: "Actor", cell: ({ row }) => <div>{row.original.actorIdentifier || "System"}<p className="text-xs text-muted-foreground">{row.original.actorRole || "Background process"}</p></div> },
	{ accessorKey: "resourceType", header: "Resource", cell: ({ row }) => <div>{row.original.resourceType || "—"}<p className="max-w-48 truncate font-mono text-xs" title={row.original.resourceId}>{row.original.resourceId}</p></div> },
	{ id: "details", header: "Evidence", cell: ({ row }) => <details className="min-w-48 max-w-xl"><summary className="cursor-pointer text-sm text-primary">View event details</summary><EventDetails event={row.original} /></details> },
];

function EventDetails({ event }: { event: AuditEvent }) {
	return <div className="space-y-4 py-4 whitespace-normal">
		<dl className="grid gap-3">
			<Detail label="Event ID">{event.id}</Detail>
			<Detail label="Actor ID">{event.actorId || "—"}</Detail>
			<Detail label="Organization">{event.organization || "—"}</Detail>
			<Detail label="Resource ID">{event.resourceId || "—"}</Detail>
			<Detail label="Request">{event.httpMethod} {event.httpPath || "Background event"}</Detail>
			<Detail label="HTTP status">{event.httpStatus ?? "—"}</Detail>
			<Detail label="IP address">{event.ipAddress || "—"}</Detail>
			<Detail label="Correlation ID">{event.correlationId}</Detail>
		</dl>
		<Link className="text-sm text-primary underline" to="/dashboard/audit" search={{ page: 1, page_size: 20, correlation_id: event.correlationId }}>Follow correlated events</Link>
		{event.resourceType === "FHIRExport" && event.resourceId && <p><Link className="text-sm text-primary underline" to="/dashboard/fhir/exports/$exportId" params={{ exportId: event.resourceId }} search={{ page: 1, page_size: 20 }}>View FHIR export</Link></p>}
		{event.resourceType === "FHIRValidationResult" && event.resourceId && <p><Link className="text-sm text-primary underline" to="/dashboard/fhir/validations/$validationId" params={{ validationId: event.resourceId }} search={{ page: 1, page_size: 20 }}>View validation</Link></p>}
		<JsonDetails value={event.details} />
	</div>;
}

function AuditEventsPage() {
	const { items, pagination } = Route.useLoaderData().data;
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const router = useRouter();
	const loading = useRouterState({ select: (state) => state.status === "pending" });
	const update = (changes: Partial<typeof search>) => { void navigate({ search: (previous) => ({ ...previous, ...changes }), resetScroll: false }); };
	return <div className="flex flex-col gap-6">
		<header className="flex flex-wrap items-start justify-between gap-4"><div><h1 className="text-2xl font-semibold tracking-tight">Audit events</h1><p className="mt-1 text-sm text-muted-foreground">Review security and processing evidence, inspect outcomes and trace related FHIR activity.</p></div><Button variant="outline" disabled={loading} onClick={() => void router.invalidate()}>Refresh</Button></header>
		<form key={JSON.stringify(search)} className="grid gap-4 rounded-xl border bg-card p-5 sm:grid-cols-2 xl:grid-cols-3" onSubmit={(event) => {
			event.preventDefault();
			const values = Object.fromEntries(new FormData(event.currentTarget));
			update(auditSearchSchema.parse({ ...values, page: 1, page_size: search.page_size }));
		}}>
			{([
				["action", "Action", "FHIR_VALIDATION_REQUESTED"],
				["resource_type", "Resource type", "FHIRValidationResult"],
				["resource_id", "Resource ID", "Exact resource identifier"],
				["actor_id", "Actor ID", "Numeric user ID"],
				["correlation_id", "Correlation ID", "Correlation UUID"],
			] as const).map(([name, label, placeholder]) => <label key={name} className="space-y-2 text-sm font-medium">{label}<input className="w-full rounded-md border bg-background px-3 py-2 font-normal" name={name} defaultValue={search[name] ?? ""} placeholder={placeholder} pattern={name === "actor_id" ? "[1-9][0-9]*" : name === "correlation_id" ? "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}" : undefined} /></label>)}
			<label className="space-y-2 text-sm font-medium">Outcome<select name="outcome" defaultValue={search.outcome ?? ""} className="w-full rounded-md border bg-background px-3 py-2 font-normal"><option value="">All outcomes</option><option value="SUCCESS">Success</option><option value="FAILURE">Failure</option><option value="DENIED">Denied</option></select></label>
			<div className="flex gap-2 sm:col-span-2 xl:col-span-3"><Button type="submit" disabled={loading}>Apply filters</Button><Button type="button" variant="outline" disabled={loading} onClick={() => void navigate({ search: { page: 1, page_size: search.page_size } })}>Clear filters</Button></div>
		</form>
		<DataTable columns={columns} data={items} getRowId={(event) => event.id} pagination={pagination} isLoading={loading} emptyMessage="No audit events match these filters." onPageChange={(page) => update({ page })} onPageSizeChange={(page_size) => update({ page: 1, page_size })} />
	</div>;
}
