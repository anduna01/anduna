"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV } from "@/lib/nav";

export const CURRENT_PHASE = 2;

export function Sidebar() {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1 p-3 text-sm">
      <div className="px-3 pb-4 pt-2">
        <div className="text-base font-semibold tracking-tight">Viral Clip Factory</div>
        <div className="text-xs text-muted">Fábrica semiautomática de clips</div>
      </div>
      {NAV.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        const pending = item.phase > CURRENT_PHASE;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center justify-between rounded-md px-3 py-2 transition-colors ${
              active ? "bg-accent/10 font-medium text-accent" : "hover:bg-border/50"
            }`}
          >
            <span>{item.label}</span>
            {pending && <span className="text-[10px] text-muted">F{item.phase}</span>}
          </Link>
        );
      })}
    </nav>
  );
}
