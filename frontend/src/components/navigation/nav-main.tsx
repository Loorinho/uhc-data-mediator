import { Link } from "@tanstack/react-router";
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

	return (
		<SidebarGroup>
			<SidebarGroupContent>
				<SidebarMenu>
					{items.map((item) => (
						<SidebarMenuItem key={item.title}>
							<SidebarMenuButton
								tooltip={item.title}
								className="h-10 transition-colors data-[active=true]:bg-primary data-[active=true]:font-semibold data-[active=true]:text-primary-foreground data-[active=true]:shadow-sm data-[active=true]:hover:bg-primary/90 data-[active=true]:hover:text-primary-foreground"
								render={
									<Link
										to={item.url}
										activeProps={{ "data-active": true }}
										onClick={() => {
											if (isMobile) {
												setOpenMobile(false);
											}
										}}

                                        activeOptions={{
											exact: !(
												item.url.includes("/users") ||
												item.url.includes("/roles") ||
												item.url.includes("/products")
											),
										}}
										
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
