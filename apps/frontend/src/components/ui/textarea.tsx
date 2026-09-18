import * as React from "react";
import { cn } from "@/lib/utils";

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "flex min-h-28 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-pretty text-slate-900 placeholder:text-slate-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#1E3A8A] disabled:opacity-50 aria-invalid:border-red-500",
        className
      )}
      {...props}
    />
  );
}

export { Textarea };
