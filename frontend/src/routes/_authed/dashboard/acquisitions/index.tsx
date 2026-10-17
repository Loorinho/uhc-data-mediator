import { createFileRoute, redirect, useRouter, useRouterState } from "@tanstack/react-router";
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
	acquisitionSearchSchema,
	getAcquisitionsFn,
	triggerAcquisitionFn,
} from "@/server-functions/acquisition.api";
import type { AcquisitionMode, AcquisitionStatus } from "@/types/types";
import { acquisitionColumns } from "./-columns";
import { AcquisitionError } from "./-error";

export const Route = createFileRoute("/_authed/dashboard/acquisitions/")({
	validateSearch: (search) => acquisitionSearchSchema.parse(search),
	beforeLoad: ({ context }) => {
		const roles = context.user.user?.roles ?? [];
		if (!roles.includes("data_provider")) {
			throw redirect({ to: "/dashboard" });
		}
	},
	loaderDeps: ({ search }) => search,
	loader: ({ deps }) => getAcquisitionsFn({ data: deps }),
	errorComponent: AcquisitionError,
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
	const { items: attempts, pagination, statuses, modes } = response.data;
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
					</DropdownMenuContent>
				</DropdownMenu>
			</div>

			<div className="flex flex-wrap items-end gap-3 rounded-lg border bg-muted/20 p-4">
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Status
					<select
						className="min-w-40 rounded-md border bg-background px-3 py-2"
						value={search.status ?? ""}
						disabled={isLoading}
						onChange={(event) =>
							updateSearch({
								status: (event.target.value || undefined) as
									| AcquisitionStatus
									| undefined,
								page: 1,
							})
						}
					>
						<option value="">All statuses</option>
						{Array.from(
							new Set([
								...(statuses ?? []),
								...(search.status ? [search.status] : []),
							]),
						).map((value) => (
							<option key={value} value={value}>
								{value}
							</option>
						))}
					</select>
				</label>
				<label className="flex flex-col gap-1.5 text-sm font-medium">
					Mode
					<select
						className="min-w-40 rounded-md border bg-background px-3 py-2"
						value={search.mode ?? ""}
						disabled={isLoading}
						onChange={(event) =>
							updateSearch({
								mode: (event.target.value || undefined) as
									| AcquisitionMode
									| undefined,
								page: 1,
							})
						}
					>
						<option value="">All modes</option>
						{Array.from(
							new Set([
								...(modes ?? []),
								...(search.mode ? [search.mode] : []),
							]),
						).map((value) => (
							<option key={value} value={value}>
								{value}
							</option>
						))}
					</select>
				</label>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() =>
						updateSearch({ page: 1, status: undefined, mode: undefined })
					}
				>
					Clear filters
				</Button>
				<Button
					variant="outline"
					disabled={isLoading}
					onClick={() => void router.invalidate()}
				>
					Refresh
				</Button>
			</div>
			<DataTable
				columns={acquisitionColumns}
				data={attempts}
				emptyMessage="No acquisition attempts match these filters."
				pagination={pagination}
				isLoading={isLoading}
				getRowId={(attempt) => attempt.acquisitionId}
				onPageChange={(page) => updateSearch({ page })}
				onPageSizeChange={(page_size) => updateSearch({ page_size, page: 1 })}
				onRowClick={(attempt) =>
					void router.navigate({
						to: "/dashboard/acquisitions/$acquisitionId",
						params: { acquisitionId: attempt.acquisitionId },
						search: { page: 1, page_size: 20, include_raw: false },
					})
				}
			/>
		</div>
	);
}
