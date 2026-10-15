import { Link } from "@tanstack/react-router";
import {
	Badge,
	BellIcon,
	Building2,
	CommandIcon,
	HomeIcon,
	Podium,
	RefreshCcwDot,
	ShieldCogCorner,
	SunSnow,
	Trophy,
	UserGroupIcon,
	Users2,
} from "lucide-react";
import type * as React from "react";
import {
	Sidebar,
	SidebarContent,
	SidebarFooter,
	SidebarHeader,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
} from "@/components/ui/sidebar";

import { useAuth } from "@/lib/auth";
import { getDefaultRoute, getNavigationItems, type NavigationKey } from "./navigator";
import { NavMain } from "./nav-main";

const navigationIcons: Record<NavigationKey, React.ReactNode> = {
	users: <Users2 />,
	roles: <ShieldCogCorner />,
	dashboard: <HomeIcon />,
	products: <Podium />,

};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
	const { user } = useAuth();
	const items = user
		? getNavigationItems(user).map((item) => ({
				...item,
				icon: navigationIcons[item.key],
			}))
		: [];

	return (
		<Sidebar collapsible="icon" {...props}>
			<SidebarHeader>
				<SidebarMenu>
					<SidebarMenuItem>
						<SidebarMenuButton
							className="data-[slot=sidebar-menu-button]:p-1.7!"
							render={
								<Link
									to={user ? getDefaultRoute(user) : "/dashboard"}
									aria-label="UHC Data Mediator"
									className="py-2"
								>
									<img
										src="/images/speedykom-long.png"
										alt="SpeedyKom logo"
										className="size-10 md:w-full group-data-[state=collapsed]:hidden"
									/>
									<img
                                    src="/images/speedykom-short.jpeg"
										alt="SpeedyKom logo"
										className="hidden size-full group-data-[state=collapsed]:block"
									/>
								</Link>
							}
						>
							<CommandIcon className="w-full" />
						</SidebarMenuButton>
					</SidebarMenuItem>
				</SidebarMenu>
			</SidebarHeader>
			<SidebarContent>{user && <NavMain items={items} />}</SidebarContent>
			{/* <SidebarFooter>{user ? <NavUser user={user} /> : null}</SidebarFooter> */}
		</Sidebar>
	);
}
