import { getCurrentUser } from '@/server-functions/auth.api';
import { createFileRoute, redirect } from '@tanstack/react-router'

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
})

