import { createFileRoute, Link, redirect, useRouter, useRouterState } from "@tanstack/react-router";
import { type ColumnDef, tableFeatures } from "@tanstack/react-table";
import type { ReactNode } from "react";
import { DataTable } from "@/components/data-table";
import {
	Accordion,
	AccordionContent,
	AccordionItem,
	AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDateTime } from "@/lib/utils";
import {
	acquisitionDetailSearchSchema,
	getAcquisitionDetailFn,
} from "@/server-functions/acquisition.api";
import type { AcquisitionObservation } from "@/types/types";
import { AcquisitionStatusBadge } from "./-columns";
import { AcquisitionError } from "./-error";
import { useAppForm } from "@/hooks/form";
import { canonicalTransformationSchema, triggerCanonicalTransformation } from "@/server-functions/transformation.api";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "@/components/ui/toast";
import { RefreshCcwDot } from "lucide-react";

export const Route = createFileRoute(
	"/_authed/dashboard/acquisitions/$acquisitionId",
)({
	validateSearch: (search) => acquisitionDetailSearchSchema.parse(search),
	beforeLoad: ({ context }) => {
		const roles = context.user.user?.roles ?? [];
		if (!roles.includes("data_provider")) {
			throw redirect({ to: "/dashboard" });
		}
	},
	loaderDeps: ({ search }) => search,
	loader: ({ params, deps }) =>
		getAcquisitionDetailFn({
			data: { acquisitionId: params.acquisitionId, ...deps },
		}),
	component: AcquisitionDetails,
	errorComponent: AcquisitionError,
	head: () => ({
		meta: [{ title: "Acquisition details · UHC Data Mediator" }],
	}),
});

const features = tableFeatures({});

const DATA_PRODUCT_OPTIONS = [
	{
		label: "Sierra Leone district ANC activity",
		value: "sl-district-anc-activity",
	},
];
const observationColumns: ColumnDef<typeof features, AcquisitionObservation>[] =
	[
		{
			accessorKey: "orgUnitName",
			header: "Organisation unit",
			cell: ({ row }) => row.original.orgUnitName || row.original.orgUnitId,
		},
		{
			accessorKey: "measureName",
			header: "Measure",
			cell: ({ row }) => row.original.measureName || row.original.measureId,
		},
		{ accessorKey: "measureType", header: "Type" },
		{ accessorKey: "period", header: "Period" },
		{ accessorKey: "value", header: "Value" },
		{
			accessorKey: "dimensions",
			header: "Dimensions",
			cell: ({ row }) => (
				<code className="text-xs">
					{JSON.stringify(row.original.dimensions)}
				</code>
			),
		},
	];

function Detail({ label, children }: { label: string; children: ReactNode }) {
	return (
		<div className="min-w-0 space-y-1">
			<dt className="text-sm text-muted-foreground">{label}</dt>
			<dd className="break-words text-sm font-medium">{children}</dd>
		</div>
	);
}

function JsonDetails({ value }: { value: unknown }) {
	return (
		<pre className="max-h-96 overflow-auto rounded-md bg-muted p-4 text-xs leading-relaxed">
			{JSON.stringify(value, null, 2)}
		</pre>
	);
}

function AcquisitionDetails() {
	const { data: attempt } = Route.useLoaderData();
	const search = Route.useSearch();
	const navigate = Route.useNavigate();
	const router = useRouter();
	const isLoading = useRouterState({ select: (state) => state.status === "pending" });
	const updateSearch = (changes: Partial<typeof search>) => {
		void navigate({
			search: (previous) => ({ ...previous, ...changes }),
			resetScroll: false,
		});
	};

	const canonicalDataTransformationForm = useAppForm({
		defaultValues: {
			acquisitionId: attempt.acquisitionId,
			productCode: "sl-district-anc-activity",
		},
		validators: {
			onSubmit: canonicalTransformationSchema,
		},
		onSubmit: async ({value}) => {
			try {
				const response = await triggerCanonicalTransformation({
					data: value
				});
				
				if(response.statusCode !== 200){
					toast.add({
						title: "Error",
						description: response.message,
						type: "error"
					})
					return;
				}

				toast.add({
					title: "Transformation triggered",
					description: response.message ?? "Canonical transformation has been queued successfully.",
					type: "success"
				})

				void router.invalidate();
			} catch (error) {
				toast.add({
					title: "Error",
					description: "Failed to trigger canonical transformation.",
					type: "error"
				})
			}
		},
	})
	return (
		<div className="flex flex-col gap-6">
			<div className="flex flex-wrap items-center justify-between gap-3">
				<div className="space-y-2">
					<Link
						className="text-sm text-muted-foreground"
						to="/dashboard/acquisitions"
						search={{ page: 1, page_size: 10 }}
					>
						← All acquisitions
					</Link>
					<h1 className="text-2xl text-primary font-semibold">Acquisition details</h1>
				
				</div>

			
					
					<div className="flex items-center gap-3">
						<RefreshCcwDot
							className="h-4 w-4 cursor-pointer"
							onClick={() => void router.invalidate()}
						/>
						<form
							onSubmit={async (event) => {
								event.preventDefault();
								event.stopPropagation();

								await canonicalDataTransformationForm.handleSubmit();
							}}
						>
							<div className="flex items-end gap-2">
								<canonicalDataTransformationForm.AppField name="productCode">
									{(field) => (
										<field.SelectInput
											label="Data product"
											id="productCode"
											className="w-64"
											items={DATA_PRODUCT_OPTIONS}
										/>
									)}
								</canonicalDataTransformationForm.AppField>
								<canonicalDataTransformationForm.Subscribe
									selector={(state) => ({ isSubmitting: state.isSubmitting })}
								>
									{({ isSubmitting }) => (
										<Button type="submit" disabled={isSubmitting}>
											{isSubmitting ? (
												<>
													<Spinner data-icon="inline-start" />
													Transforming…
												</>
											) : (
												"Trigger transformation"
											)}
										</Button>
									)}
								</canonicalDataTransformationForm.Subscribe>
							</div>
						</form>
					</div>
				
			</div>

			<section className="space-y-5 rounded-xl border bg-card p-6">
				<div className="flex flex-wrap items-center gap-2">
					<AcquisitionStatusBadge status={attempt.status} />
					<Badge variant="secondary">{attempt.mode}</Badge>
					{attempt.outcome && (
						<Badge variant="outline">{attempt.outcome}</Badge>
					)}
				</div>
				<dl className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
					<Detail label="Source">{attempt.source}</Detail>
					<Detail label="Requested">
						{formatDateTime(attempt.requestedAt)}
					</Detail>
					<Detail label="Started">{formatDateTime(attempt.startedAt)}</Detail>
					<Detail label="Finished">{formatDateTime(attempt.finishedAt)}</Detail>
					<Detail label="Duration">
						{attempt.durationMs === null
							? "—"
							: `${attempt.durationMs.toLocaleString()} ms`}
					</Detail>
					<Detail label="Records saved / received">
						{attempt.recordsSaved} / {attempt.recordsReceived}
					</Detail>
					<Detail label="Received / expected combinations">
						{attempt.receivedCombinations} / {attempt.expectedCombinations}
					</Detail>
					<Detail label="HTTP status">{attempt.httpStatusCode ?? "—"}</Detail>
					<div className="sm:col-span-2">
						<Detail label="Correlation ID">{attempt.correlationId}</Detail>
					</div>
				</dl>
				{attempt.errorMessage && (
					<div
						role="alert"
						className="rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"
					>
						{attempt.errorMessage}
					</div>
				)}
			</section>

			<Accordion
				defaultValue={["observations"]}
				className="rounded-xl border bg-card px-5"
			>
				<AccordionItem value="configuration">
					<AccordionTrigger>Acquisition configuration</AccordionTrigger>
					<AccordionContent>
						<JsonDetails value={attempt.configuration} />
					</AccordionContent>
				</AccordionItem>
				<AccordionItem value="observations">
					<AccordionTrigger>
						Observations (
						{attempt.observations.pagination.totalItems.toLocaleString()})
					</AccordionTrigger>
					<AccordionContent>
						<DataTable
							columns={observationColumns}
							data={attempt.observations.items}
							getRowId={(item) => item.observationId}
							emptyMessage="No observations were saved for this acquisition."
							pagination={attempt.observations.pagination}
							isLoading={isLoading}
							onPageChange={(page) => updateSearch({ page })}
							onPageSizeChange={(page_size) =>
								updateSearch({ page: 1, page_size })
							}
						/>
					</AccordionContent>
				</AccordionItem>
				<AccordionItem value="missing">
					<AccordionTrigger>
						Missing combinations ({attempt.missingCombinations.length})
					</AccordionTrigger>
					<AccordionContent>
						{attempt.missingCombinations.length ? (
							<JsonDetails value={attempt.missingCombinations} />
						) : (
							<p className="text-muted-foreground">
								No missing combinations were recorded.
							</p>
						)}
					</AccordionContent>
				</AccordionItem>
				<AccordionItem value="request">
					<AccordionTrigger>Upstream request</AccordionTrigger>
					<AccordionContent>
						<p className="mb-3 break-all text-sm text-muted-foreground">
							{attempt.apiUrl || "No upstream request URL recorded."}
						</p>
						<JsonDetails value={attempt.requestPayload} />
					</AccordionContent>
				</AccordionItem>
				<AccordionItem value="response">
					<AccordionTrigger>Raw DHIS2 response</AccordionTrigger>
					<AccordionContent>
						<p className="mb-3 text-sm text-muted-foreground">
							Raw responses can be large and are loaded only on request.
						</p>
						{attempt.responsePayload !== undefined ? (
							<JsonDetails value={attempt.responsePayload} />
						) : (
							<Button
								variant="outline"
								disabled={isLoading}
								onClick={() => updateSearch({ include_raw: true })}
							>
								{isLoading ? "Loading…" : "Load raw response"}
							</Button>
						)}
					</AccordionContent>
				</AccordionItem>
			</Accordion>
		</div>
	);
}
