import { Badge } from "@/components/ui/badge";
import type {
	DistrictMappingStatus,
	QualityStatus,
	ReleaseStatus,
	TransformationStatus,
} from "@/types/types";

const releaseStatusVariant = {
	DRAFT: "outline",
	VALIDATING: "secondary",
	READY: "secondary",
	PUBLISHED: "default",
	REJECTED: "destructive",
} as const;

export function ReleaseStatusBadge({ status }: { status: ReleaseStatus }) {
	return <Badge variant={releaseStatusVariant[status]}>{status}</Badge>;
}

const transformationStatusVariant = {
	PENDING: "outline",
	RUNNING: "secondary",
	SUCCEEDED: "default",
	FAILED: "destructive",
} as const;

export function TransformationStatusBadge({
	status,
}: {
	status: TransformationStatus;
}) {
	return (
		<Badge variant={transformationStatusVariant[status]}>{status}</Badge>
	);
}

const qualityStatusVariant = {
	NOT_CHECKED: "outline",
	PASSED: "default",
	WARNING: "secondary",
	FAILED: "destructive",
} as const;

export function QualityStatusBadge({ status }: { status: QualityStatus }) {
	return <Badge variant={qualityStatusVariant[status]}>{status}</Badge>;
}

const mappingStatusVariant: Record<
	DistrictMappingStatus,
	"default" | "secondary" | "outline" | "destructive"
> = {
	MAPPED: "default",
	UNMAPPED: "outline",
	AMBIGUOUS: "secondary",
	IGNORED: "destructive",
};

export function MappingStatusBadge({
	status,
}: {
	status: DistrictMappingStatus;
}) {
	return <Badge variant={mappingStatusVariant[status]}>{status}</Badge>;
}

export function ActiveBadge({ active }: { active: boolean }) {
	return (
		<Badge variant={active ? "default" : "outline"}>
			{active ? "Active" : "Inactive"}
		</Badge>
	);
}

export function SensitivityBadge({
	sensitivity,
}: {
	sensitivity: "PUBLIC" | "INTERNAL" | "RESTRICTED";
}) {
	const variant =
		sensitivity === "PUBLIC"
			? "default"
			: sensitivity === "INTERNAL"
				? "secondary"
				: "destructive";
	return <Badge variant={variant}>{sensitivity}</Badge>;
}
