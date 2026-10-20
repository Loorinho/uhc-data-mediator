import type { ReactNode } from "react";

export function Detail({ label, children }: { label: string; children: ReactNode }) {
	return (
		<div className="min-w-0 space-y-1">
			<dt className="text-sm text-muted-foreground">{label}</dt>
			<dd className="break-words text-sm font-medium">{children}</dd>
		</div>
	);
}

export function JsonDetails({ value }: { value: unknown }) {
	return (
		<pre className="max-h-96 overflow-auto rounded-md bg-muted p-4 text-xs leading-relaxed">
			{JSON.stringify(value, null, 2)}
		</pre>
	);
}
