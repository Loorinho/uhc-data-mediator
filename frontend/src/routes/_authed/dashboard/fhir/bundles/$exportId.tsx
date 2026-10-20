import { createFileRoute, Link } from "@tanstack/react-router";
import { FHIRDocumentView, FHIRHeading } from "@/components/fhir/shared";
import { PageError } from "@/components/page-error";
import { getFHIRBundleFn } from "@/server-functions/fhir.api";

export const Route = createFileRoute("/_authed/dashboard/fhir/bundles/$exportId")({
	loader: ({ params }) => getFHIRBundleFn({ data: params }),
	errorComponent: PageError,
	head: () => ({ meta: [{ title: "FHIR bundle JSON · UHC Data Mediator" }] }),
	component: BundlePage,
});

function BundlePage() {
	const { exportId } = Route.useParams();
	return <div className="flex flex-col gap-6"><Link className="text-sm text-muted-foreground" to="/dashboard/fhir/exports/$exportId" params={{ exportId }} search={{ page: 1, page_size: 20 }}>← Export details</Link><FHIRHeading title="FHIR bundle" description="Inspect or download the generated JSON bundle. The API verifies the stored bundle checksum before serving this file." /><FHIRDocumentView file={Route.useLoaderData()} /></div>;
}