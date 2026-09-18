"use client";

import type { ComponentType } from "react";
import Link from "next/link";
import { DropdownMenu as DropdownMenuPrimitive } from "radix-ui";
import { ChevronDown } from "lucide-react";
import { useHoverDropdown } from "@/components/shared/useHoverDropdown";

// Top-level nav entries; every other authenticated entry lives in the Practice menu so the bar fits.
export const PRIMARY_NAV_HREFS = ["/home", "/competency", "/courses", "/quiz"];

interface NavItem {
  href: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  badge?: string;
  badgeColor?: string;
}

export function PracticeMenu({ items, isActive }: { items: NavItem[]; isActive: (path: string) => boolean }) {
  const dropdown = useHoverDropdown();
  const active = items.some((item) => isActive(item.href));
  return (
    <div {...dropdown.triggerProps}>
      <DropdownMenuPrimitive.Root modal={false} open={dropdown.open} onOpenChange={dropdown.onOpenChange}>
        <DropdownMenuPrimitive.Trigger
          className={`relative flex items-center gap-1.5 whitespace-nowrap rounded-md px-2 py-2 text-xs font-medium outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A] xl:px-2.5 xl:text-sm ${
            active ? "font-bold text-[#1E3A8A]" : "text-slate-600 hover:text-[#1E3A8A]"
          }`}
        >
          Practice
          <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
        </DropdownMenuPrimitive.Trigger>
        <DropdownMenuPrimitive.Portal>
          <DropdownMenuPrimitive.Content
            {...dropdown.contentProps}
            align="start"
            sideOffset={8}
            className="z-50 min-w-64 rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg"
          >
            {items.map(({ href, label, icon: Icon, badge, badgeColor }) => (
              <DropdownMenuPrimitive.Item key={href} asChild>
                <Link
                  href={href}
                  className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm outline-none data-[highlighted]:bg-slate-100 ${
                    isActive(href) ? "font-semibold text-[#1E3A8A]" : "text-slate-700"
                  }`}
                >
                  <Icon className="h-4 w-4 text-slate-400" aria-hidden="true" />
                  <span className="flex-1">{label}</span>
                  {badge && (
                    <span className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${badgeColor ?? ""}`}>{badge}</span>
                  )}
                </Link>
              </DropdownMenuPrimitive.Item>
            ))}
          </DropdownMenuPrimitive.Content>
        </DropdownMenuPrimitive.Portal>
      </DropdownMenuPrimitive.Root>
    </div>
  );
}
