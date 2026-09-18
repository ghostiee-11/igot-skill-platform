import * as React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "secondary" | "outline" | "ghost" | "danger" | "saffron";
  size?: "sm" | "md" | "lg" | "icon";
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", children, ...props }, ref) => {
    const variants = {
      default: "bg-[#1E3A8A] text-white hover:bg-[#1D3557] shadow-sm focus-visible:ring-[#1E3A8A]",
      secondary: "bg-slate-100 text-slate-800 hover:bg-slate-200 focus-visible:ring-slate-400",
      outline: "border border-slate-300 text-slate-700 bg-transparent hover:bg-slate-50 focus-visible:ring-slate-400",
      ghost: "text-slate-700 hover:bg-slate-100 focus-visible:ring-slate-400",
      danger: "bg-rose-600 text-white hover:bg-rose-700 shadow-sm focus-visible:ring-rose-500",
      saffron: "bg-amber-600 text-white hover:bg-amber-700 shadow-sm focus-visible:ring-amber-500 font-semibold",
    };

    const sizes = {
      sm: "h-8 px-3 text-xs rounded-md",
      md: "h-10 px-4 text-sm rounded-lg",
      lg: "h-12 px-6 text-base rounded-lg font-medium",
      icon: "h-10 w-10 p-0 rounded-lg flex items-center justify-center",
    };

    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center gap-2 font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer select-none",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
