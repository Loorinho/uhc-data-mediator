import { createFileRoute, redirect, useRouter } from "@tanstack/react-router";
import { ChevronDownIcon } from "lucide-react";
import { useState } from "react";

import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "@/components/ui/toast";
import {
	getAcquisitionsFn,
	triggerAcquisitionFn,
} from "@/server-functions/acquisition.api";
import type { AcquisitionMode } from "@/types/types";
import { acquisitionColumns } from "./-columns";

export const Route = createFileRoute("/_authed/dashboard/acquisitions/")({
	beforeLoad: ({ context }) => {
		const roles = context.user.user?.roles ?? [];
		if (!roles.includes("data_provider")) {
			throw redirect({ to: "/dashboard" });
		}
	},
	loader: () => getAcquisitionsFn(),
	component: RouteComponent,
	head: () => ({
		meta: [
			{
				title: "UHC Data Mediator - Data Acquisitions",
			},
		],
	}),
});

function RouteComponent() {
	const response = Route.useLoaderData();
	const attempts = response?.data ?? [];
	const router = useRouter();

	const [open, setOpen] = useState(false);
	const [pendingMode, setPendingMode] = useState<AcquisitionMode | null>(null);

	const triggerAcquisition = async (mode: AcquisitionMode) => {
		setPendingMode(mode);

		try {
			const result = await triggerAcquisitionFn({ data: { mode } });

			if (result?.statusCode === 200 || result?.statusCode === 202) {
				toast.add({
					title: "Acquisition queued",
					description: result.message,
				});
				setOpen(false);
				await router.invalidate();
			} else {
				toast.add({
					title: "Acquisition failed",
					description:
						result?.message ?? "The acquisition could not be started.",
				});
			}
		} catch (error) {
			toast.add({
				title: "Acquisition failed",
				description:
					error instanceof Error
						? error.message
						: "An unexpected error occurred.",
			});
		} finally {
			setPendingMode(null);
		}
	};

	return (
		<div className="flex flex-col gap-4">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-2xl font-semibold">Data Acquisitions</h1>
					<p className="text-sm text-muted-foreground">
						DHIS2 data acquisition attempts
					</p>
				</div>

				<DropdownMenu
					open={open}
					onOpenChange={(nextOpen) => {
						if (pendingMode === null) setOpen(nextOpen);
					}}
				>
					<DropdownMenuTrigger
						render={
							<Button disabled={pendingMode !== null}>
								Trigger Acquisition
								<ChevronDownIcon data-icon="inline-end" />
							</Button>
						}
					/>
					<DropdownMenuContent align="end">
						<DropdownMenuItem
							disabled={pendingMode !== null}
							closeOnClick={false}
							onClick={() => {
								void triggerAcquisition("LIVE");
							}}
						>
							{pendingMode === "LIVE" ? <Spinner /> : null}
							LIVE acquisition
						</DropdownMenuItem>
						<DropdownMenuItem
							disabled={pendingMode !== null}
							closeOnClick={false}
							onClick={() => {
								void triggerAcquisition("FIXTURE");
							}}
						>
							{pendingMode === "FIXTURE" ? <Spinner /> : null}
							FIXTURE acquisition
						</DropdownMenuItem>
					</DropdownMenuContent>
				</DropdownMenu>
			</div>

			<DataTable
				columns={acquisitionColumns}
				data={attempts}
				emptyMessage="No acquisition attempts yet."
			/>
		</div>
	);
}
