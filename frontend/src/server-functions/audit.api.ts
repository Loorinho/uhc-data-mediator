import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { canViewAuditEvents } from "@/lib/permissions";
import type { AuditEvent } from "@/types/audit";
import type { PaginatedItems } from "@/types/types";
import { getCurrentUser } from "./auth.api";
import { getExplorationData } from "./exploration.server";

const optionalText = z.string().trim().optional().catch(undefined);
export const auditSearchSchema = z.object({
	page: z.coerce.number().int().min(1).catch(1),
	page_size: z.coerce.number().int().min(1).max(100).catch(20),
	action: optionalText,
	outcome: z.enum(["SUCCESS", "FAILURE", "DENIED"]).optional().catch(undefined),
	actor_id: z.string().regex(/^[1-9]\d*$/).optional().catch(undefined),
	resource_type: optionalText,
	resource_id: optionalText,
	correlation_id: z.uuid().optional().catch(undefined),
});

export type AuditSearch = z.infer<typeof auditSearchSchema>;

export const getAuditEventsFn = createServerFn({ method: "GET" })
	.validator(auditSearchSchema)
	.handler(async ({ data }) => {
		const { user } = await getCurrentUser();
		if (!canViewAuditEvents(user)) throw new Error("Only auditors may view audit events.");
		return getExplorationData<PaginatedItems<AuditEvent>>("audit-events/", data);
	});