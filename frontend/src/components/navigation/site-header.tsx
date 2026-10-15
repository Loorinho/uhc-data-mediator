import {
	Breadcrumb,
	BreadcrumbItem,
	BreadcrumbLink,
	BreadcrumbList,
	BreadcrumbPage,
	BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuGroup,
	DropdownMenuItem,
	DropdownMenuLabel,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOutIcon } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Link, useLocation } from "@tanstack/react-router";
import { Fragment } from "react";
import { useAuth } from "@/lib/auth";
import { getDefaultRoute } from "./navigator";

export function SiteHeader() {
	const { pathname } = useLocation();
	const { user, logout } = useAuth();

	const breadcrumbItems = (() => {
		const segments = pathname.split("/").filter(Boolean);

		if (segments.length === 0) return [];

		const root = segments[0];
		const defaultRoute = user ? getDefaultRoute(user) : "/dashboard";

		const items: { label: string; path: string }[] = [
			{
				label: root === "admin" || defaultRoute !== "/dashboard" ? "Admin" : "Home",
				path: defaultRoute,
			},
		];

		let currentPath = `/${root}`;

		for (const segment of segments.slice(1)) {
			currentPath += `/${segment}`;

			items.push({
				label: segment
					.split("-")
					.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
					.join(" "),
				path: currentPath,
			});
		}

		return items;
	})();

	return (
		<header className="flex h-12 shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12 justify-between px-4">
			<div className="flex min-w-0 flex-1 items-center gap-1 px-0 sm:px-4 lg:gap-2 lg:px-6">
				<SidebarTrigger className="-ml-1" />
				<Separator
					orientation="vertical"
					className="mx-2 h-4 data-vertical:self-auto"
				/>
				<Breadcrumb className="min-w-0 max-w-full">
					<BreadcrumbList className="flex-nowrap overflow-hidden">
						{breadcrumbItems.map((item, index) => {
							const isLast = index === breadcrumbItems.length - 1;

							return (
								<Fragment key={item.path}>
									<BreadcrumbItem>
										{isLast ? (
											<BreadcrumbPage className="block max-w-[55vw] truncate sm:max-w-none">
												{item.label}
											</BreadcrumbPage>
										) : (
											<BreadcrumbLink render={<Link to={item.path} />}>
												{item.label}
											</BreadcrumbLink>
										)}
									</BreadcrumbItem>

									{!isLast && <BreadcrumbSeparator />}
								</Fragment>
							);
						})}
					</BreadcrumbList>
				</Breadcrumb>
			</div>

			<div className="flex shrink-0 items-center gap-2">
				{/* <ModeToggle /> */}
				{user && (
					<DropdownMenu>
						<DropdownMenuTrigger
							render={
								<button
									type="button"
									aria-label="User menu"
									className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring"
								/>
							}
						>
							<Avatar className="size-8">
								<AvatarFallback>
									{user.username.charAt(0).toUpperCase()}
								</AvatarFallback>
							</Avatar>
						</DropdownMenuTrigger>
						<DropdownMenuContent
							className="min-w-56"
							align="end"
							sideOffset={8}
						>
							<DropdownMenuGroup>
								<DropdownMenuLabel className="grid gap-0.5 text-sm">
									<span className="truncate font-medium text-foreground">
										{user.username}
									</span>
									<span className="truncate text-xs font-normal text-muted-foreground">
										Role: {user.roles[0]}
									</span>
								
								</DropdownMenuLabel>
							</DropdownMenuGroup>
							<DropdownMenuSeparator />
							<DropdownMenuItem
								onClick={async () => {
									await logout();
								}}
								className="text-destructive"
							>
								<LogOutIcon />
								Log out
							</DropdownMenuItem>
						</DropdownMenuContent>
					</DropdownMenu>
				)}
			</div>
		</header>
	);
}
