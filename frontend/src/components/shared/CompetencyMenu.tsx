"use client";

import Link from "next/link";
import { DropdownMenu as DropdownMenuPrimitive } from "radix-ui";
import { ChevronDown, LayoutGrid, Target } from "lucide-react";
import { DOMAINS, DOMAIN_ACCENT_CLASS, DOMAIN_ORDER } from "@/features/competency/domains";
import { useHoverDropdown } from "@/components/shared/useHoverDropdown";

const itemClass =
  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm outline-none data-[highlighted]:bg-slate-100";

export function CompetencyMenu({ pathname }: { pathname: string }) {
  const dropdown = useHoverDropdown();
  const onDomain = (code: string) => pathname === `/competency/${code}`;
  const onProfile = pathname === "/competency";
  const active = pathname === "/competency" || pathname.startsWith("/competency/");

  return (
    <div {...dropdown.triggerProps}>
      <DropdownMenuPrimitive.Root modal={false} open={dropdown.open} onOpenChange={dropdown.onOpenChange}>
        <DropdownMenuPrimitive.Trigger
          className={`relative flex items-center gap-1.5 whitespace-nowrap rounded-md px-2 py-2 text-xs font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A] xl:px-2.5 xl:text-sm ${
            active ? "font-bold text-[#1E3A8A]" : "text-slate-600 hover:text-[#1E3A8A]"
          }`}
        >
          <Target className={`h-3.5 w-3.5 ${active ? "text-[#1E3A8A]" : "text-slate-400"}`} aria-hidden="true" />
          Competency
          <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
        </DropdownMenuPrimitive.Trigger>
        <DropdownMenuPrimitive.Portal>
          <DropdownMenuPrimitive.Content
            {...dropdown.contentProps}
            align="start"
            sideOffset={8}
            className="z-50 min-w-72 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg"
          >
            <DropdownMenuPrimitive.Item asChild>
              <Link href="/competency" className={`${itemClass} ${onProfile ? "font-semibold text-[#1E3A8A]" : "text-slate-700"}`}>
                <LayoutGrid className="h-4 w-4 text-slate-400" aria-hidden="true" />
                <span className="flex-1">
                  <span className="block">Competency profile</span>
                  <span className="block text-xs font-normal text-slate-500">Your levels and gaps across all domains</span>
                </span>
              </Link>
            </DropdownMenuPrimitive.Item>
            <DropdownMenuPrimitive.Separator className="my-1 h-px bg-slate-100" />
            <DropdownMenuPrimitive.Label className="px-3 pb-1 pt-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Domains
            </DropdownMenuPrimitive.Label>
            {DOMAIN_ORDER.map((code) => {
              const meta = DOMAINS[code];
              const Icon = meta.icon;
              return (
                <DropdownMenuPrimitive.Item key={code} asChild>
                  <Link
                    href={`/competency/${code}`}
                    className={`${itemClass} ${onDomain(code) ? "font-semibold text-[#1E3A8A]" : "text-slate-700"}`}
                  >
                    <span className={`size-2 rounded-full ${DOMAIN_ACCENT_CLASS[code]}`} aria-hidden="true" />
                    <Icon className="h-4 w-4 text-slate-400" aria-hidden="true" />
                    <span className="flex-1">{meta.label}</span>
                  </Link>
                </DropdownMenuPrimitive.Item>
              );
            })}
          </DropdownMenuPrimitive.Content>
        </DropdownMenuPrimitive.Portal>
      </DropdownMenuPrimitive.Root>
    </div>
  );
}
