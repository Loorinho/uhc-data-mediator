import { AppSidebar } from '@/components/navigation/app-sidebar';
import { SiteHeader } from '@/components/navigation/site-header';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { getCurrentUser } from '@/server-functions/auth.api';
import { createFileRoute, Outlet, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/_authed')({
  beforeLoad: async ({ location, context }) => {
		const user = await getCurrentUser();

		if (!user.user) {
			throw redirect({
				to: "/",
				search: { redirect: location.href },
			});
		}
		return { user };
	},
	component: RouteComponent,
});

function RouteComponent() {
	return (
		<SidebarProvider>
			<AppSidebar variant="inset" />
			<SidebarInset className="min-w-0 overflow-x-hidden">
				<SiteHeader />
				<main className="w-full min-w-0 max-w-full py-4 md:gap-6 md:py-6 px-3 [&_[data-slot=table-container]]:max-w-full">
					<Outlet />
				</main>
			</SidebarInset>
		</SidebarProvider>
	);
}

