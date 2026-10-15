import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useFieldContext } from "@/hooks/form-context";
import { cn } from "@/lib/utils";
import { Field, FieldError } from "../ui/field";
import { Input } from "../ui/input";

export default function TextInput({
	label,
	description,
	id,
	autoFocus = false,
	type = "text",
	required = false,
	className,
	value,
}: {
	label?: string;
	id: string;
	description?: string;
	type?: string;
	autoFocus?: boolean;
	required?: boolean;
	value?: string;
	className?: string;
}) {
	const field = useFieldContext<string>();
	const [isPasswordVisible, setIsPasswordVisible] = useState(false);

	const isInvalid = field.state.meta.isTouched && !field.state.meta.isValid;
	const isPasswordField = type === "password";
	const inputType = isPasswordField && isPasswordVisible ? "text" : type;

	return (
		<Field data-invalid={isInvalid} className="relative gap-0">
			<div className="relative">
				<Input
					id={id}
					type={inputType}
					placeholder=" "
					name={field.name}
					value={value ?? field.state.value}
					onBlur={() => {
						field.handleBlur();
					}}
					aria-invalid={isInvalid}
					onChange={(e) => field.handleChange(e.target.value)}
					autoComplete="off"
					autoFocus={autoFocus}
					className={cn("peer", isPasswordField && "pr-12", className)}
				/>
				{isPasswordField && (
					<button
						type="button"
						aria-label={isPasswordVisible ? "Hide password" : "Show password"}
						aria-pressed={isPasswordVisible}
						onClick={() => setIsPasswordVisible((visible) => !visible)}
						className="absolute right-3 top-1/2 z-10 -translate-y-1/2 text-muted-foreground cursor-pointer transition-colors hover:text-primary"
					>
						{isPasswordVisible ? (
							<EyeOff className="size-4" />
						) : (
							<Eye className="size-4" />
						)}
					</button>
				)}
				{label && (
					<label
						htmlFor={id}
						className={cn(
							"pointer-events-none absolute left-1 top-1/2 z-10 -translate-y-1/2 px-1 text-sm text-muted-foreground transition-all duration-150 peer-focus:top-0 peer-focus:-translate-y-2.6 peer-focus:scale-75 peer-focus:bg-white peer-focus:text-primary peer-[&:not(:placeholder-shown)]:top-0 peer-[&:not(:placeholder-shown)]:-translate-y-2.6 peer-[&:not(:placeholder-shown)]:scale-75 peer-[&:not(:placeholder-shown)]:text-primary peer-[&:not(:placeholder-shown)]:bg-white ",
						)}
					>
						{label}
						{required ? <span className="text-destructive"> *</span> : null}
					</label>
				)}
			</div>
			{description && (
				<p className="mt-1 text-sm text-muted-foreground">{description}</p>
			)}
			{isInvalid && (
				<FieldError>
					{field.state.meta.errors.map((error) => error?.message).join(", ")}
				</FieldError>
			)}
		</Field>
	);
}
