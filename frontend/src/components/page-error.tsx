import {
	type ErrorComponentProps,
	useRouter,
} from "@tanstack/react-router";
import { Button } from "@/components/ui/button";

export function PageError({ error, reset }: ErrorComponentProps) {
	const router = useRouter();
	return (
		<div role="alert" className="space-y-4 rounded-lg border p-6">
			<h1 className="text-lg font-semibold">Unable to load this page</h1>
			<p className="text-sm text-muted-foreground">
				{error instanceof Error
					? error.message
					: "An unexpected error occurred."}
			</p>
			<Button
				variant="outline"
				onClick={() => void router.invalidate().then(reset)}
			>
				Try again
			</Button>
		</div>
	);
}
