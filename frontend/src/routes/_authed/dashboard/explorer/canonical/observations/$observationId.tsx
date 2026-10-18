import { createFileRoute, Link } from "@tanstack/react-router";

import { Detail, JsonDetails } from "@/components/detail";
import { PageError } from "@/components/page-error";
import { Badge } from "@/components/ui/badge";
import { formatDateTime } from "@/lib/utils";
import { getCanonicalObservationDetailFn } from "@/server-functions/canonical.api";

export const Route = createFileRoute(
	"/_authed/dashboard/explorer/canonical/observations/$observationId",
)({
	loader: ({ params }) =>
		getCanonicalObservationDetailFn({
			data: { observationId: params.observationId },
		}),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Canonical observation · UHC Data Mediator" }],
	}),
});

function RouteComponent() {
	const { data: observation } = Route.useLoaderData();

	return (
		<div className="flex flex-col gap-6">
			<div className="space-y-2">
				<Link
					className="text-sm text-muted-foreground"
					to="/dashboard/explorer/canonical/observations"
					search={{ page: 1, page_size: 20 }}
				>
					← All canonical observations
				</Link>
				<h1 className="text-2xl font-semibold text-primary">
					{observation.measure.name}
				</h1>
			</div>

			<section className="space-y-5 rounded-xl border bg-card p-6">
				<div className="flex flex-wrap items-center gap-2">
					<Badge variant="secondary">{observation.source_type}</Badge>
					<Badge variant="outline">Schema {observation.schema_version}</Badge>
				</div>
				<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
					<Detail label="District">{observation.district.name}</Detail>
					<Detail label="Measure">
						{observation.measure.name} ({observation.measure.code})
					</Detail>
					<Detail label="Period">
						{observation.period} · {observation.period_type}
					</Detail>
					<Detail label="Value">{observation.value}</Detail>
					<Detail label="Transformed">
						{formatDateTime(observation.transformed_at)}
					</Detail>
					<Detail label="Release">
						<Link
							className="font-mono text-xs underline underline-offset-4"
							to="/dashboard/products/releases/$releaseId"
							params={{ releaseId: observation.release }}
							search={{ page: 1, page_size: 20 }}
						>
							{observation.release}
						</Link>
					</Detail>
				</dl>
				{Object.keys(observation.dimensions).length > 0 && (
					<div className="space-y-2">
						<h2 className="text-sm font-medium">Dimensions</h2>
						<JsonDetails value={observation.dimensions} />
					</div>
				)}
			</section>
		</div>
	);
}
