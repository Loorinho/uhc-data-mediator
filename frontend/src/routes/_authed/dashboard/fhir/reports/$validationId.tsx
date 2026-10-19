import { createFileRoute, Link } from "@tanstack/react-router";
import { FHIRDocumentView, FHIRHeading } from "@/components/fhir/shared";
import { PageError } from "@/components/page-error";
import { getFHIRReportFn } from "@/server-functions/fhir.api";

export const Route = createFileRoute("/_authed/dashboard/fhir/reports/$validationId")({
	loader: ({ params }) => getFHIRReportFn({ data: params }),
	errorComponent: PageError,
	head: () => ({ meta: [{ title: "Conformity report · UHC Data Mediator" }] }),
	component: ReportPage,
});

function ReportPage() {
	const { validationId } = Route.useParams();
	return <div className="flex flex-col gap-6"><Link className="text-sm text-muted-foreground" to="/dashboard/fhir/validations/$validationId" params={{ validationId }} search={{ page: 1, page_size: 20 }}>← Validation details</Link><FHIRHeading title="Conformity report" description="View the validation evidence and download the original JSON report. A failed validation may not have produced a report; the API will report if the file is unavailable." /><FHIRDocumentView file={Route.useLoaderData()} /></div>;
}