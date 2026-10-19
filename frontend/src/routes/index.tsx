import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {  FieldGroup } from '@/components/ui/field'
import { Spinner } from '@/components/ui/spinner'
import { toast } from '@/components/ui/toast'
import { useAppForm } from '@/hooks/form'
import { useAuth } from '@/lib/auth'
import { getCurrentUser, loginFn } from '@/server-functions/auth.api'
import { createFileRoute, redirect, useNavigate, useRouter } from '@tanstack/react-router'
import {z} from "zod"

export const Route = createFileRoute('/')({
  // Users who already have a session should never see the login page —
  // send them straight to the dashboard instead.
  beforeLoad: async () => {
		const { user } = await getCurrentUser();

		if (user) {
			throw redirect({ to: user.roles.includes("admin") ? "/dashboard/users" : "/dashboard" });
		}
	},
  component: Home,
  head: () => ({
		meta: [
			{
				title: "UHC Data Mediator - Login",
			},
		],
	}),

})

export const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

function Home() {

	const auth = useAuth(); 

  const navigate = useNavigate();
  const router = useRouter()
  const form = useAppForm({
    defaultValues: {
      username: "",
      password: "",
    },
    validators: {
      onSubmit: loginSchema
    },
    onSubmit: async ({value}) => {

      try{

        const response = await loginFn({
          data: value,
        })

        if(response?.statusCode !== 200){
        toast.add({
            title: "Login Failed",
            description: response?.message ?? "An error occurred while logging in.",
          })

          return
        }

		await auth.refresh();
		await router.invalidate();

        // Redirect to authenticated route
        await navigate({ to: response.data.roles.includes("admin") ? "/dashboard/users" : "/dashboard" });

      }catch(error){
        toast.add({
          title: "Login Failed",
          description:
            error instanceof Error
              ? error.message
              : "An unexpected error occurred while logging in.",
        })
      }
    },
  });
  return (
   <div className="flex justify-center items-center h-screen" >
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center mb-5">
			<div className="flex justify-center items-center h-20">

			<img src="/images/speedykom-long.png" alt="UHC Data Mediator Logo" className="w-50"/>
			</div>
          <CardTitle className="text-xl text-primary">Welcome back</CardTitle>
          <CardDescription>
            Login with your UHC Data Mediator account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
          onSubmit={async (event) => {
					event.preventDefault();
					event.stopPropagation();

					await form.handleSubmit();
				}}
          >
            <FieldGroup>
             
             <form.AppField name="username">
						{(field) => (
							<field.TextInput
								label="Username"
								id="username"
								autoFocus
								required
							/>
						)}
					</form.AppField>

           <form.AppField name="password">
						{(field) => (
							<field.TextInput
								label="Password"
								id="password"
								type="password"
								autoFocus
								required
							/>
						)}
					</form.AppField>
           	<form.Subscribe
					selector={(state) => ({
						username: state.values.username,
						password: state.values.password,
						// type: state.values.type,
						isSubmitting: state.isSubmitting,
					})}
				>
					{/* {({ email, password, type: selectedType, isSubmitting }) => { */}
					{({ username, password, isSubmitting }) => {
						const fieldsProvided = Boolean(
							// email?.trim() && password?.trim() && selectedType?.trim(),
							username?.trim() && password?.trim(),
						);

						return (
							<Button
								type="submit"
								size="lg"
								disabled={isSubmitting || !fieldsProvided}
								className="mt-1 w-full"
							>
								{isSubmitting ? (
									<>
										<Spinner data-icon="inline-start" />
										Logging in...
									</>
								) : (
									"Login"
								)}
							</Button>
						);
					}}
				</form.Subscribe>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
     
    </div>
  )
}
