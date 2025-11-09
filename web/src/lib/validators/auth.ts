import { z } from "zod";

export const signInSchema = z.object({
  email: z.string().email("Please enter a valid email address."),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters.")
    .max(128, "Password must be 128 characters or fewer."),
});

export type SignInInput = z.infer<typeof signInSchema>;

export const signUpSchema = z
  .object({
    name: z
      .string()
      .min(2, "Name must be at least 2 characters.")
      .max(64, "Name must be 64 characters or fewer."),
    email: z.string().email("Please enter a valid email address."),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .max(128, "Password must be 128 characters or fewer.")
      .regex(
        /^(?=.*[A-Za-z])(?=.*\d).+$/,
        "Password must include at least one letter and one number.",
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export type SignUpInput = z.infer<typeof signUpSchema>;


