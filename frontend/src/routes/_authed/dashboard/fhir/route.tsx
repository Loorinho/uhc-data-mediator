import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { canViewFHIR } from "@/lib/permissions";

export const Route = createFileRoute("/_authed/dashboard/fhir")({
	beforeLoad: ({ context }) => {
		if (!canViewFHIR(context.user.user)) throw redirect({ to: "/dashboard" });
	},
	component: Outlet,
});