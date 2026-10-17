export { cn } from "cn"



const formatter = new Intl.DateTimeFormat("en-UG", {
	dateStyle: "medium",
	timeStyle: "short",
	timeZone: "Africa/Kampala",
});

/**
 * Formats an ISO/GMT date string for display in Africa/Kampala time.
 * Returns "-" for null/undefined values.
 */
export function formatDateTime(value: string | null | undefined): string {
	if (!value) return "-";
	return formatter.format(new Date(value));
}
