import * as React from "react";
import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return <div aria-hidden="true" className={cn("rounded-lg bg-slate-200/70", className)} {...props} />;
}

export { Skeleton };
