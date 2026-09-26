"use client";

import type { ReactNode } from "react";

// Validated with the dataviz skill's validate_palette.js on the white card surface (all checks pass;
// aqua and yellow sit below 3:1 contrast, so every chart ships a table view as relief).
export const CHART = {
  series: ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],
  neutral: "#c3c2b7",
  status: { good: "#0ca30c", warning: "#fab219", serious: "#ec835a" },
  grid: "#e1e0d9",
  axis: "#c3c2b7",
  muted: "#898781",
  secondaryInk: "#52514e",
  surface: "#ffffff",
};

export const axisTick = { fill: CHART.muted, fontSize: 12 };

type Shape = "rect" | "line";

function Key({ color, shape }: { color: string; shape: Shape }) {
  return (
    <span
      aria-hidden="true"
      className={shape === "line" ? "h-0.5 w-4 shrink-0 rounded-full" : "size-3 shrink-0 rounded-sm"}
      style={{ backgroundColor: color }}
    />
  );
}

export function ChartLegend({ items }: { items: { label: string; color: string; shape?: Shape }[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-slate-600">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-2">
          <Key color={item.color} shape={item.shape ?? "rect"} />
          {item.label}
        </li>
      ))}
    </ul>
  );
}

interface TooltipEntry {
  name?: string | number;
  value?: number | string;
  color?: string;
  dataKey?: string | number;
}

export function ChartTooltip({
  active,
  payload,
  label,
  format = (v: number) => String(v),
  shape = "rect",
}: {
  active?: boolean;
  payload?: TooltipEntry[];
  label?: ReactNode;
  format?: (v: number) => string;
  shape?: Shape;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm shadow-md">
      <p className="mb-1 text-xs text-slate-500">{label}</p>
      <ul className="space-y-1">
        {payload.map((entry) => (
          <li key={String(entry.dataKey)} className="flex items-center gap-2">
            <Key color={entry.color ?? CHART.neutral} shape={shape} />
            <span className="font-semibold text-slate-900 tabular-nums">
              {typeof entry.value === "number" ? format(entry.value) : entry.value}
            </span>
            <span className="text-slate-500">{entry.name}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ChartTable({ caption, columns, rows }: { caption: string; columns: string[]; rows: (string | number)[][] }) {
  return (
    <details className="text-sm">
      <summary className="cursor-pointer text-slate-600 hover:text-slate-900">View as table</summary>
      <div className="mt-2 overflow-x-auto">
        <table className="w-full border-collapse text-left">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr>
              {columns.map((column) => (
                <th key={column} scope="col" className="border-b border-slate-200 py-2 pr-4 font-medium text-slate-700">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) =>
                  j === 0 ? (
                    <th key={j} scope="row" className="border-b border-slate-100 py-2 pr-4 font-normal text-slate-700">
                      {cell}
                    </th>
                  ) : (
                    <td key={j} className="border-b border-slate-100 py-2 pr-4 text-slate-900 tabular-nums">
                      {cell}
                    </td>
                  )
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}
