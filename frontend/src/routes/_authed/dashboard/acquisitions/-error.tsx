import {
	type ErrorComponentProps,
	Link,
	useRouter,
} from "@tanstack/react-router";
import { Button } from "@/components/ui/button";

export function AcquisitionError({ error, reset }: ErrorComponentProps) {
	const router = useRouter();
	return (
		<div role="alert" className="space-y-4 rounded-lg border p-6">
			<h1 className="text-lg font-semibold">Unable to load acquisition data</h1>
			<p className="text-sm text-muted-foreground">
				{error instanceof Error
					? error.message
					: "An unexpected error occurred."}
			</p>
			<div className="flex gap-4">
				<Button
					variant="outline"
					onClick={() => void router.invalidate().then(reset)}
				>
					Try again
				</Button>
				<Link
					className="self-center text-sm underline"
					to="/dashboard/acquisitions"
					search={{ page: 1, page_size: 10 }}
				>
					Back to acquisitions
				</Link>
			</div>
		</div>
	);
}
