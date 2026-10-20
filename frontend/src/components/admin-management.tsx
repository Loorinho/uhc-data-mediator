import { useState } from "react";
import { Link, useRouter, type ErrorComponentProps } from "@tanstack/react-router";
import { ShieldCheck, UserPlus, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { toast } from "@/components/ui/toast";
import { useAppForm } from "@/hooks/form";
import {
	Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
	createRoleFn, createRoleSchema, registerUserFn, registerUserSchema,
	type ManagedRole, type ManagedUser,
} from "@/server-functions/admin.api";

type Props = { kind: "users" | "roles"; roles: ManagedRole[]; users?: ManagedUser[] };

export function AdminManagement({ kind, users = [], roles }: Props) {
	const isUsers = kind === "users";
	const [search, setSearch] = useState("");
	const filteredUsers = users.filter((user) =>
		`${user.username} ${user.roles.join(" ")}`.toLowerCase().includes(search.toLowerCase()),
	);
	const filteredRoles = roles.filter((role) => role.name.toLowerCase().includes(search.toLowerCase()));

	return (
		<div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
			<header className="flex flex-wrap items-start justify-between gap-4">
				<div>
					<p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><ShieldCheck className="size-4" /> Administration</p>
					<h1 className="text-3xl font-semibold tracking-tight">{isUsers ? "Users" : "Roles"}</h1>
					<p className="mt-2 text-sm text-muted-foreground">{isUsers ? "Manage accounts and assign access to the data mediator." : "Manage the roles available when registering users."}</p>
				</div>
				<Badge variant="secondary">Admin access only</Badge>
			</header>
			<div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
				<section className="min-w-0 rounded-xl border bg-card shadow-sm" aria-label={isUsers ? "Existing users" : "Existing roles"}>
					<div className="flex flex-wrap items-center justify-between gap-3 border-b p-5">
						<h2 className="flex items-center gap-2 font-semibold">{isUsers ? <Users className="size-4" /> : <ShieldCheck className="size-4" />}All {kind}<Badge variant="secondary">{isUsers ? users.length : roles.length}</Badge></h2>
						<Input className="w-full sm:w-60" type="search" aria-label={`Search ${kind}`} placeholder={`Search ${kind}…`} value={search} onChange={(event) => setSearch(event.target.value)} />
					</div>
					<Table>
						<TableHeader><TableRow><TableHead className="pl-5">{isUsers ? "Username" : "Name"}</TableHead><TableHead>{isUsers ? "Assigned roles" : "Role ID"}</TableHead></TableRow></TableHeader>
						<TableBody>
							{isUsers ? filteredUsers.map((user) => (
								<TableRow key={user.id}><TableCell className="py-4 pl-5 font-medium">{user.username}</TableCell><TableCell><div className="flex flex-wrap gap-1">{user.roles.length ? user.roles.map((role) => <Badge key={role} variant="secondary">{role}</Badge>) : <span className="text-muted-foreground">No roles assigned</span>}</div></TableCell></TableRow>
							)) : filteredRoles.map((role) => (
								<TableRow key={role.id}><TableCell className="py-4 pl-5 font-medium">{role.name}</TableCell><TableCell className="text-muted-foreground">{role.id}</TableCell></TableRow>
							))}
							{(isUsers ? filteredUsers : filteredRoles).length === 0 && <TableRow><TableCell colSpan={2} className="py-12 text-center text-muted-foreground">{search ? "No matches found." : `No ${kind} yet.`}</TableCell></TableRow>}
						</TableBody>
					</Table>
				</section>
				<section className="rounded-xl border bg-card p-5 shadow-sm">
					<h2 className="flex items-center gap-2 text-lg font-semibold">{isUsers ? <UserPlus className="size-5" /> : <ShieldCheck className="size-5" />}{isUsers ? "Register user" : "Create role"}</h2>
					<p className="mt-2 text-sm text-muted-foreground">{isUsers ? "Create an account with one existing role." : "Use a clear name such as analyst or data_provider."}</p>
					{isUsers ? <RegisterUserForm roles={roles} /> : <CreateRoleForm />}
					<p className="mt-5 border-t pt-4 text-xs text-muted-foreground">{isUsers ? <>Need another role? <Link to="/dashboard/roles" className="font-medium text-primary underline">Manage roles</Link></> : <>New roles do not automatically grant application permissions. <Link to="/dashboard/users" className="font-medium text-primary underline">Manage users</Link></>}</p>
				</section>
			</div>
		</div>
	);
}

function RegisterUserForm({ roles }: { roles: ManagedRole[] }) {
	const router = useRouter();
	const form = useAppForm({
		defaultValues: { username: "", password: "", role: "" },
		validators: { onSubmit: registerUserSchema },
		onSubmit: async ({ value }) => {
			try {
				await registerUserFn({ data: value });
				form.reset();
				toast.add({ title: "User registered" });
				await router.invalidate();
			} catch (cause) {
				toast.add({
					title: "Unable to register user",
					description: cause instanceof Error ? cause.message : "Please try again.",
				});
			}
		},
	});

	return (
		<form
			className="mt-5 flex flex-col gap-4"
			noValidate
			onSubmit={(event) => {
				event.preventDefault();
				event.stopPropagation();
				void form.handleSubmit();
			}}
		>
			<form.Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
				{([canSubmit, isSubmitting]) => (
					<>
						<fieldset disabled={isSubmitting} className="flex min-w-0 flex-col gap-4 disabled:opacity-60">
							<form.AppField name="username">
								{(field) => <field.TextInput id="new-user-username" label="Username" required />}
							</form.AppField>
							<form.AppField name="password">
								{(field) => <field.TextInput id="new-user-password" label="Password" type="password" required description="At least 8 characters. Share securely with the user." />}
							</form.AppField>
							<form.AppField name="role">
								{(field) => <field.SelectInput id="new-user-role" label="Role" items={roles.map((role) => ({ label: role.name, value: role.name }))} disabled={isSubmitting || roles.length === 0} />}
							</form.AppField>
							{roles.length === 0 && <p className="text-sm text-muted-foreground">Create a role before registering a user.</p>}
						</fieldset>
						<Button type="submit" disabled={!canSubmit || isSubmitting || roles.length === 0}>
							{isSubmitting && <Spinner />}{isSubmitting ? "Saving…" : "Register user"}
						</Button>
					</>
				)}
			</form.Subscribe>
		</form>
	);
}

function CreateRoleForm() {
	const router = useRouter();
	const form = useAppForm({
		defaultValues: { name: "" },
		validators: { onSubmit: createRoleSchema },
		onSubmit: async ({ value }) => {
			try {
				await createRoleFn({ data: value });
				form.reset();
				toast.add({ title: "Role created" });
				await router.invalidate();
			} catch (cause) {
				toast.add({
					title: "Unable to create role",
					description: cause instanceof Error ? cause.message : "Please try again.",
				});
			}
		},
	});

	return (
		<form
			className="mt-5 flex flex-col gap-4"
			noValidate
			onSubmit={(event) => {
				event.preventDefault();
				event.stopPropagation();
				void form.handleSubmit();
			}}
		>
			<form.Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
				{([canSubmit, isSubmitting]) => (
					<>
						<fieldset disabled={isSubmitting} className="min-w-0 disabled:opacity-60">
							<form.AppField name="name">
								{(field) => <field.TextInput id="new-role-name" label="Role name" required />}
							</form.AppField>
						</fieldset>
						<Button type="submit" disabled={!canSubmit || isSubmitting}>
							{isSubmitting && <Spinner />}{isSubmitting ? "Saving…" : "Create role"}
						</Button>
					</>
				)}
			</form.Subscribe>
		</form>
	);
}

export function AdminPageError({ error, reset }: ErrorComponentProps) {
	const router = useRouter();
	return <div role="alert" className="rounded-xl border p-6"><h1 className="text-xl font-semibold">Unable to load administration</h1><p className="my-3 text-sm text-muted-foreground">{error instanceof Error ? error.message : "An unexpected error occurred."}</p><Button onClick={() => { void router.invalidate().then(reset); }}>Try again</Button></div>;
}