import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const variants = {
  default: "bg-[#1E3A8A] text-white hover:bg-[#1D3557] shadow-sm focus-visible:ring-[#1E3A8A]",
  outline: "border border-slate-300 text-slate-700 bg-transparent hover:bg-slate-50 focus-visible:ring-slate-400",
  ghost: "text-slate-700 hover:bg-slate-100 focus-visible:ring-slate-400",
};

const sizes = {
  sm: "h-8 px-3 text-xs rounded-md",
  md: "h-10 px-4 text-sm rounded-lg",
};

type ButtonLinkProps = React.ComponentProps<typeof Link> & {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
};

export function ButtonLink({ className, variant = "default", size = "md", ...props }: ButtonLinkProps) {
  return (
    <Link
      className={cn(
        "inline-flex items-center justify-center gap-2 font-medium transition-colors select-none focus-visible:outline-none focus-visible:ring-2",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    />
  );
}
