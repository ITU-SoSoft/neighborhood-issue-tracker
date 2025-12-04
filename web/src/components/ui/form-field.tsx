import * as React from "react";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";

interface FormFieldProps {
  /** Unique ID for the input - used for label association */
  id: string;
  /** Label text */
  label: string;
  /** Error message to display */
  error?: string;
  /** Helper text to display below the input */
  description?: string;
  /** Whether the field is required */
  required?: boolean;
  /** Additional class names for the wrapper */
  className?: string;
  /** The form input element */
  children: React.ReactElement<{ "aria-invalid"?: string; "aria-describedby"?: string }>;
}

export function FormField({
  id,
  label,
  error,
  description,
  required,
  className,
  children,
}: FormFieldProps) {
  const errorId = error ? `${id}-error` : undefined;
  const descriptionId = description ? `${id}-description` : undefined;
  const describedBy = [errorId, descriptionId].filter(Boolean).join(" ") || undefined;

  // Clone the child element to add accessibility attributes
  const enhancedChildren = React.cloneElement(children, {
    "aria-invalid": error ? "true" : undefined,
    "aria-describedby": describedBy,
  });

  return (
    <div className={cn("space-y-2", className)}>
      <Label
        htmlFor={id}
        className={cn(error && "text-destructive")}
      >
        {label}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      {enhancedChildren}
      {description && !error && (
        <p id={descriptionId} className="text-sm text-muted-foreground">{description}</p>
      )}
      {error && (
        <p id={errorId} className="text-sm text-destructive" role="alert">{error}</p>
      )}
    </div>
  );
}
