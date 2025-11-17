import { SignInInput, SignUpInput } from "@/lib/validators/auth";

const AUTH_BASE_URL =
  process.env.NEXT_PUBLIC_AUTH_BASE_URL?.replace(/\/$/, "") ?? "/api/auth";

console.log("AUTH_BASE_URL", AUTH_BASE_URL);

async function handleResponse<T>(response: Response) {
  if (!response.ok) {
    let message = "Unexpected error. Please try again.";

    try {
      const payload = (await response.json()) as { message?: string };
      if (payload?.message) {
        message = payload.message;
      }
    } catch {
      // ignore json parse errors
    }

    throw new Error(message);
  }

  try {
    return (await response.json()) as T;
  } catch {
    return {} as T;
  }
}

export async function signInRequest(input: SignInInput) {
  const response = await fetch(`${AUTH_BASE_URL}/sign-in/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
    credentials: "include",
  });

  return handleResponse<{ redirectTo?: string }>(response);
}

export async function signUpRequest(input: SignUpInput) {
  const response = await fetch(`${AUTH_BASE_URL}/sign-up/email`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name: input.name,
      email: input.email,
      password: input.password,
    }),
    credentials: "include",
  });

  return handleResponse<{ redirectTo?: string }>(response);
}



