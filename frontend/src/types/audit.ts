import type { JsonValue } from "./types";

export type AuditEvent = {
	id: string;
	actorId: string | null;
	actorIdentifier: string;
	actorRole: string;
	organization: string;
	action: string;
	resourceType: string;
	resourceId: string;
	outcome: "SUCCESS" | "FAILURE" | "DENIED";
	httpMethod: string;
	httpPath: string;
	httpStatus: number | null;
	correlationId: string;
	ipAddress: string | null;
	details: JsonValue;
	createdAt: string;
};