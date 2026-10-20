import { useEffect, useTransition, type ReactNode } from "react";
import { useRouter } from "@tanstack/react-router";
import { Download, RefreshCw } from "lucide-react";
import { useAppForm } from "@/hooks/form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "@/components/ui/toast";
import type { FHIRDocument } from "@/types/fhir";

export function FHIRStatus({ value }: { value: string | null }) {
	const destructive = ["FAILED", "NON_CONFORMANT", "BLOCKED", "fatal", "error"].includes(value ?? "");
	return <Badge variant={destructive ? "destructive" : "secondary"}>{value?.replaceAll("_", " ") || "Not classified"}</Badge>;
}

export function FHIRAction({ label, action, disabled = false }: {
	label: string;
	action: () => Promise<void>;
	disabled?: boolean;
}) {
	const form = useAppForm({
		defaultValues: {},
		onSubmit: async () => {
			try { await action(); }
			catch (error) {
				toast.add({ title: `${label} failed`, description: error instanceof Error ? error.message : "Please try again." });
			}
		},
	});
	return <form onSubmit={(event) => { event.preventDefault(); event.stopPropagation(); void form.handleSubmit(); }}>
		<form.Subscribe selector={(state) => state.isSubmitting}>
			{(isSubmitting) => <Button type="submit" disabled={disabled || isSubmitting}>{isSubmitting && <Spinner />}{isSubmitting ? "Queuing…" : label}</Button>}
		</form.Subscribe>
	</form>;
}

export function FHIRRefresh({ active = false }: { active?: boolean }) {
	const router = useRouter();
	const [pending, startTransition] = useTransition();
	useEffect(() => {
		if (!active) return;
		let refreshing = false;
		const timer = setInterval(() => {
			if (document.visibilityState !== "visible" || refreshing) return;
			refreshing = true;
			void router.invalidate().catch(() => {}).finally(() => { refreshing = false; });
		}, 5000);
		return () => clearInterval(timer);
	}, [active, router]);
	return <div className="flex items-center gap-3">
		{active && <span role="status" className="text-xs text-muted-foreground">Job in progress · refreshing every 5 seconds</span>}
		<Button variant="outline" disabled={pending} onClick={() => startTransition(async () => { await router.invalidate(); })}><RefreshCw className={pending ? "size-4 animate-spin" : "size-4"} />Refresh</Button>
	</div>;
}

export function FHIRHeading({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
	return <header className="flex flex-wrap items-start justify-between gap-4"><div className="space-y-2"><p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Interoperability · FHIR R4</p><h1 className="text-2xl font-semibold text-primary">{title}</h1><p className="max-w-2xl text-sm text-muted-foreground">{description}</p></div><div className="flex flex-wrap items-center gap-2">{children}</div></header>;
}

export function FHIRDocumentView({ file }: { file: FHIRDocument }) {
	function download() {
		const url = URL.createObjectURL(new Blob([file.text], { type: "application/json" }));
		const link = document.createElement("a");
		link.href = url;
		link.download = file.filename;
		link.click();
		setTimeout(() => URL.revokeObjectURL(url), 1000);
	}
	let formatted = file.text;
	try { formatted = JSON.stringify(JSON.parse(file.text), null, 2); } catch { /* Show original file if not JSON. */ }
	return <section className="space-y-4 rounded-xl border bg-card p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="break-all text-sm font-medium">{file.filename}</h2><Button onClick={download}><Download className="size-4" />Download JSON</Button></div><pre tabIndex={0} aria-label="JSON document" className="max-h-[70vh] overflow-auto rounded-md bg-muted p-4 text-xs leading-relaxed">{formatted}</pre></section>;
}

export function FHIRJobError({ message }: { message: string }) {
	return message ? <p role="alert" className="whitespace-pre-wrap break-words rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{message}</p> : null;
}