import { Link, useRouterState } from "@tanstack/react-router";
import { getActiveNavigationUrl } from "./navigator";
import {
	SidebarGroup,
	SidebarGroupContent,
	SidebarMenu,
	SidebarMenuButton,
	SidebarMenuItem,
	useSidebar,
} from "@/components/ui/sidebar";

export function NavMain({
	items,
}: {
	items: {
		title: string;
		url: string;
		icon?: React.ReactNode;
	}[];
}) {
	const { isMobile, setOpenMobile } = useSidebar();
	const pathname = useRouterState({ select: (state) => state.location.pathname });
	const activeUrl = getActiveNavigationUrl(pathname, items);

	return (
		<SidebarGroup>
			<SidebarGroupContent>
				<SidebarMenu>
					{items.map((item) => (
						<SidebarMenuItem key={item.title}>
							<SidebarMenuButton
								tooltip={item.title}
								isActive={item.url === activeUrl}
								className="h-10 transition-colors data-active:bg-primary data-active:font-semibold data-active:text-primary-foreground data-active:shadow-sm data-active:hover:bg-primary/90 data-active:hover:text-primary-foreground"
								render={
									<Link
										to={item.url}
										aria-current={item.url === activeUrl ? "page" : undefined}
										onClick={() => {
											if (isMobile) {
												setOpenMobile(false);
											}
										}}
										activeOptions={{ exact: true, includeSearch: false }}
									/>
								}
							>
								{item.icon}
								<span>{item.title}</span>
							</SidebarMenuButton>
						</SidebarMenuItem>
					))}
				</SidebarMenu>
			</SidebarGroupContent>
		</SidebarGroup>
	);
}
