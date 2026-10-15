import { Info } from "lucide-react";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectSeparator,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { Field, FieldDescription, FieldError } from "../ui/field";
import { useFieldContext } from "@/hooks/form-context";

export default function SelectInput({
	label,
	id,
	description,
	className,
	defaultValue,
	items,
	required = true,
	disabled = false,
	onChange,
}: {
	label: string;
	id: string;
	className?: string;
	description?: string;
	required?: boolean;
	defaultValue?: string;
	disabled?: boolean;
	onChange?: (value: string) => void;
	items: {
		label: string;
		value: string;
		toolTipText?: string;
	}[];
}) {
	const field = useFieldContext<string>();

	const isInvalid = field.state.meta.isTouched && !field.state.meta.isValid;

	const hasValue =
		typeof field.state.value === "string" &&
		field.state.value.trim().length > 0;

	return (
		<Field data-invalid={isInvalid}>
			<div className={cn("relative", className)}>
				<Select
					name={field.name}
					items={items}
					value={field.state.value || defaultValue || null}
					onValueChange={(value) => {
						if (value !== null) {
							field.handleChange(value);
							onChange?.(value);
						}
					}}
					disabled={disabled}
				>
					<SelectTrigger
						id={id}
						onBlur={field.handleBlur}
						aria-invalid={isInvalid}
						className={cn(
							"peer h-9! w-full",
							isInvalid &&
								"border-destructive focus-visible:ring-destructive/20",
						)}
					>
						<SelectValue />
					</SelectTrigger>

					<SelectContent align="center">
						<SelectSeparator />

						<TooltipProvider delay={200}>
							{items.map((item) => (
								<SelectItem key={item.value} value={item.value}>
									<div className="flex w-full items-center justify-between gap-3">
										<span>{item.label}</span>

										{item.toolTipText ? (
											<Tooltip>
												<TooltipTrigger
													render={
														<span
															tabIndex={0}
															aria-label={`Information about ${item.label}`}
															className={cn(
																"relative z-10 inline-flex size-5 shrink-0",
																"cursor-help items-center justify-center",
																"rounded-full text-muted-foreground",
																"hover:bg-muted hover:text-foreground",
															)}
															onPointerMove={(event) => {
																event.stopPropagation();
															}}
															onPointerDown={(event) => {
																event.preventDefault();
																event.stopPropagation();
															}}
															onClick={(event) => {
																event.preventDefault();
																event.stopPropagation();
															}}
														>
															<Info className="size-4" />
														</span>
													}
												/>

												<TooltipContent
													side="right"
													align="center"
													sideOffset={8}
													className="z-100 max-w-xs"
												>
													<p>{item.toolTipText}</p>
												</TooltipContent>
											</Tooltip>
										) : null}
									</div>
								</SelectItem>
							))}
						</TooltipProvider>
					</SelectContent>
				</Select>

				<label
					htmlFor={id}
					className={cn(
						"pointer-events-none absolute left-3 z-10",
						"origin-left bg-card px-1",
						"text-sm text-muted-foreground",
						"transition-all duration-150 ease-out",

						hasValue
							? "top-0 -translate-y-1/2 scale-75"
							: "top-1/2 -translate-y-1/2 scale-100",

						"peer-focus:top-0",
						"peer-focus:-translate-y-1/2",
						"peer-focus:scale-75",

						isInvalid && "text-destructive peer-focus:text-destructive",

						disabled && "cursor-not-allowed opacity-50",
					)}
				>
					{label}

					{required ? <span className="text-destructive"> *</span> : null}
				</label>
			</div>

			{description ? <FieldDescription>{description}</FieldDescription> : null}

			{isInvalid ? <FieldError errors={field.state.meta.errors} /> : null}
		</Field>
	);
}
