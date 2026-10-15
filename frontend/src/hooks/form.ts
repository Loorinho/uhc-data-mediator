import { createFormHook } from "@tanstack/react-form";
import { fieldContext, formContext } from "./form-context";
import TextInput from "@/components/form/text-input";

export const { useAppForm, withForm, withFieldGroup } = createFormHook({
	fieldContext: fieldContext,
	formContext: formContext,
	fieldComponents: {
		TextInput: TextInput,
	},
	formComponents: {},
});
