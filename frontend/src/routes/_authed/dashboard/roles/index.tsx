import { createFileRoute } from "@tanstack/react-router";
import { AdminManagement, AdminPageError } from "@/components/admin-management";
import { getRolesFn, requireAdmin } from "@/server-functions/admin.api";

export const Route = createFileRoute("/_authed/dashboard/roles/")({
  beforeLoad: () => requireAdmin(),
  loader: () => getRolesFn(),
  errorComponent: AdminPageError,
  pendingComponent: () => <p role="status" className="p-6 text-muted-foreground">Loading roles…</p>,
  head: () => ({ meta: [{ title: "Roles | UHC Data Mediator" }] }),
  component: RolesPage,
});

function RolesPage() {
  return <AdminManagement kind="roles" roles={Route.useLoaderData()} />;
}
