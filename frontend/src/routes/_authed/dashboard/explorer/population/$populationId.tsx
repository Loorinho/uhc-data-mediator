import { createFileRoute, Link } from "@tanstack/react-router";

import { Detail } from "@/components/detail";
import { PageError } from "@/components/page-error";
import { formatDateTime } from "@/lib/utils";
import { getPopulationDetailFn } from "@/server-functions/explorer.api";

export const Route = createFileRoute(
	"/_authed/dashboard/explorer/population/$populationId",
)({
	loader: ({ params }) =>
		getPopulationDetailFn({ data: { populationId: params.populationId } }),
	errorComponent: PageError,
	component: RouteComponent,
	head: () => ({
		meta: [{ title: "Population record · UHC Data Mediator" }],
	}),
});

function RouteComponent() {
	const { data: record } = Route.useLoaderData();

	return (
		<div className="flex flex-col gap-6">
			<div className="space-y-2">
				<Link
					className="text-sm text-muted-foreground"
					to="/dashboard/explorer/population"
					search={{ page: 1, page_size: 20 }}
				>
					← All population records
				</Link>
				<h1 className="text-2xl font-semibold text-primary">
					{record.district.name} · {record.reference_year}
				</h1>
			</div>

			<section className="space-y-5 rounded-xl border bg-card p-6">
				<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
					<Detail label="District">
						<Link
							className="underline underline-offset-4"
							to="/dashboard/explorer/districts/$districtId"
							params={{ districtId: record.district.id }}
						>
							{record.district.name}
						</Link>
					</Detail>
					<Detail label="Reference year">{record.reference_year}</Detail>
					<Detail label="Population">
						{record.population.toLocaleString()}
					</Detail>
					<Detail label="Source">{record.source}</Detail>
					<Detail label="Source URL">
						{record.source_url ? (
							<a
								className="break-all underline underline-offset-4"
								href={record.source_url}
								target="_blank"
								rel="noreferrer"
							>
								{record.source_url}
							</a>
						) : (
							"—"
						)}
					</Detail>
					<Detail label="Recorded">{formatDateTime(record.created_at)}</Detail>
					<div className="sm:col-span-2 xl:col-span-4">
						<Detail label="Source notes">
							{record.source_notes || "—"}
						</Detail>
					</div>
				</dl>
			</section>
		</div>
	);
}
