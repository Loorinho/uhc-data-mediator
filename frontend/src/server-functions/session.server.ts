import { getIronSession } from "iron-session";
import { getCookie, setCookie } from "@tanstack/react-start/server";

export type AuthUser = {
	username: string;
	roles: string[];
	is_superuser?: boolean;
	token: string;
	refreshToken: string;
};

export type AuthSessionData = {
	user?: AuthUser;
};

export function getAppSession(ttl = 60 * 30) {
	const password = process.env.SESSION_SECRET ?? "uhc-data-mediator-dev-secret-change-me!!";

	if (password.length < 32) {
		throw new Error("SESSION_SECRET must be at least 32 characters");
	}

	return getIronSession<AuthSessionData>(
		{ read: getCookie, write: setCookie },
		{
			cookieName: "uhc-data-mediator",
			password,
			ttl, // 30 minutes
			cookieOptions: {
				httpOnly: true,
				sameSite: "lax",
				secure: process.env.NODE_ENV === "production",
				path: "/",
			},
		},
	);
}
