import { createFileRoute } from "@tanstack/react-router";
import { AdminManagement, AdminPageError } from "@/components/admin-management";
import { getRolesFn, getUsersFn, requireAdmin } from "@/server-functions/admin.api";

export const Route = createFileRoute("/_authed/dashboard/users/")({
  beforeLoad: () => requireAdmin(),
  loader: async () => {
    const [users, roles] = await Promise.all([getUsersFn(), getRolesFn()]);
    return { users, roles };
  },
  errorComponent: AdminPageError,
  pendingComponent: () => <p role="status" className="p-6 text-muted-foreground">Loading users…</p>,
  head: () => ({ meta: [{ title: "Users | UHC Data Mediator" }] }),
  component: UsersPage,
});

function UsersPage() {
  const { users, roles } = Route.useLoaderData();
  return <AdminManagement kind="users" users={users} roles={roles} />;
}
