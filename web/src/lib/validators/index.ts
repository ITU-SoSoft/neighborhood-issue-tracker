import { z } from "zod";

// Turkish phone number validation (+90 followed by 10 digits)
const turkishPhoneRegex = /^\+90[0-9]{10}$/;

export const phoneNumberSchema = z
  .string()
  .regex(
    turkishPhoneRegex,
    "Please enter a valid Turkish phone number (+90XXXXXXXXXX)",
  );

// Request OTP schema
export const requestOTPSchema = z.object({
  phone_number: phoneNumberSchema,
});

export type RequestOTPInput = z.infer<typeof requestOTPSchema>;

// Verify OTP schema
export const verifyOTPSchema = z.object({
  phone_number: phoneNumberSchema,
  code: z
    .string()
    .length(6, "OTP code must be 6 digits")
    .regex(/^[0-9]+$/, "OTP code must contain only numbers"),
});

export type VerifyOTPInput = z.infer<typeof verifyOTPSchema>;

// Register schema - single form with all required fields
export const registerSchema = z
  .object({
    phone_number: phoneNumberSchema,
    full_name: z
      .string()
      .min(2, "Name must be at least 2 characters")
      .max(100, "Name must be 100 characters or fewer"),
    email: z.string().email("Please enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .max(128, "Password must be 128 characters or fewer")
      .regex(
        /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).+$/,
        "Password must include at least one letter, one number, and one special character",
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export type RegisterInput = z.infer<typeof registerSchema>;

// Login schema (for verified users)
export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type LoginInput = z.infer<typeof loginSchema>;

// Staff login schema (same as login, for support/manager only)
export const staffLoginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

export type StaffLoginInput = z.infer<typeof staffLoginSchema>;

// Forgot password schema
export const forgotPasswordSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
});

export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;

// Reset password schema
export const resetPasswordSchema = z
  .object({
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .max(128, "Password must be 128 characters or fewer")
      .regex(
        /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).+$/,
        "Password must include a letter, number, and special character",
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;

// Ticket schemas
export const locationSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  address: z.string().optional(),
  district: z.string().optional(),
  city: z.string().default("Istanbul"),
});

export type LocationInput = z.infer<typeof locationSchema>;

export const createTicketSchema = z.object({
  title: z
    .string()
    .min(5, "Title must be at least 5 characters")
    .max(200, "Title must be 200 characters or fewer"),
  description: z
    .string()
    .min(10, "Description must be at least 10 characters")
    .max(5000, "Description must be 5000 characters or fewer"),
  category_id: z.string().uuid("Please select a category"),
  location: locationSchema,
});

export type CreateTicketInput = z.infer<typeof createTicketSchema>;

// Comment schema
export const createCommentSchema = z.object({
  content: z
    .string()
    .min(1, "Comment cannot be empty")
    .max(2000, "Comment must be 2000 characters or fewer"),
  is_internal: z.boolean().default(false),
});

export type CreateCommentInput = z.infer<typeof createCommentSchema>;

// Feedback schema
export const createFeedbackSchema = z.object({
  rating: z
    .number()
    .min(1, "Rating must be at least 1")
    .max(5, "Rating must be at most 5"),
  comment: z
    .string()
    .max(1000, "Comment must be 1000 characters or fewer")
    .optional(),
});

export type CreateFeedbackInput = z.infer<typeof createFeedbackSchema>;

// Escalation schema
export const createEscalationSchema = z.object({
  ticket_id: z.string().uuid("Invalid ticket ID"),
  reason: z
    .string()
    .min(10, "Reason must be at least 10 characters")
    .max(2000, "Reason must be 2000 characters or fewer"),
});

export type CreateEscalationInput = z.infer<typeof createEscalationSchema>;

// Category schemas
export const createCategorySchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be 100 characters or fewer"),
  description: z
    .string()
    .max(500, "Description must be 500 characters or fewer")
    .optional(),
});

export type CreateCategoryInput = z.infer<typeof createCategorySchema>;

// User update schema
export const updateUserSchema = z.object({
  name: z
    .string()
    .min(2, "Name must be at least 2 characters")
    .max(100, "Name must be 100 characters or fewer")
    .optional(),
  email: z
    .string()
    .email("Please enter a valid email address")
    .optional()
    .or(z.literal("")),
});

export type UpdateUserInput = z.infer<typeof updateUserSchema>;
