import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "outline" | "success" | "warning" | "external" | "saffron";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "border-blue-100 bg-blue-50 text-[#1E3A8A]",
    secondary: "border-transparent bg-slate-100 text-slate-800",
    outline: "text-slate-800 border-slate-300",
    success: "border-transparent bg-emerald-100 text-emerald-800 border border-emerald-200",
    warning: "border-transparent bg-amber-100 text-amber-800 border border-amber-200",
    external: "border-transparent bg-indigo-50 text-indigo-700 border border-indigo-200",
    saffron: "border-transparent bg-amber-50 text-amber-900 border border-amber-300 font-medium",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
