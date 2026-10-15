import { createFormHook } from "@tanstack/react-form";
import { fieldContext, formContext } from "./form-context";
import TextInput from "@/components/form/text-input";
import SelectInput from "@/components/form/select-input";

export const { useAppForm, withForm, withFieldGroup } = createFormHook({
	fieldContext: fieldContext,
	formContext: formContext,
	fieldComponents: {
		TextInput: TextInput,
		SelectInput: SelectInput
	},
	formComponents: {},
});
