import { createFileRoute, Link } from "@tanstack/react-router";

import { Detail } from "@/components/detail";
import { PageError } from "@/components/page-error";
import { ActiveBadge, MappingStatusBadge } from "@/components/status-badges";
import { getDistrictDetailFn } from "@/server-functions/explorer.api";

export const Route = createFileRoute(
	"/_authed/dashboard/explorer/districts/$districtId",
)({
	loader: ({ params }) =>
		getDistrictDetailFn({ data: { districtId: params.districtId } }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "District details · UHC Data Mediator" }],
	}),
});

function RouteComponent() {
	const { data: district } = Route.useLoaderData();

	return (
		<div className="flex flex-col gap-6">
			<div className="space-y-2">
				<Link
					className="text-sm text-muted-foreground"
					to="/dashboard/explorer/districts"
					search={{ page: 1, page_size: 20 }}
				>
					← All districts
				</Link>
				<h1 className="text-2xl font-semibold text-primary">{district.name}</h1>
			</div>

			<section className="space-y-5 rounded-xl border bg-card p-6">
				<div className="flex flex-wrap items-center gap-2">
					<MappingStatusBadge status={district.mapping_status} />
					<ActiveBadge active={district.is_active} />
				</div>
				<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
					<Detail label="District code">{district.code}</Detail>
					<Detail label="DHIS2 organisation unit">
						{district.dhis2_name ?? "—"}
					</Detail>
					<Detail label="DHIS2 org unit ID">
						<code className="text-xs">
							{district.dhis2_org_unit_id ?? "—"}
						</code>
					</Detail>
					<div className="sm:col-span-2 xl:col-span-4">
						<Detail label="Mapping notes">
							{district.mapping_notes || "—"}
						</Detail>
					</div>
				</dl>
			</section>
		</div>
	);
}
