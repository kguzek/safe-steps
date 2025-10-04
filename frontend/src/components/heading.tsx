"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Footprints } from "lucide-react";

import { cn } from "@/lib/utils";

export function Heading() {
  const pathname = usePathname();

  const isMap = pathname.split("/")[1] === "map";
  return (
    <div
      className={cn(
        "absolute top-0 z-[1000] mt-24 flex w-screen justify-center transition-all delay-700 duration-1000 ease-in-out",
        {
          "mt-2.5": isMap,
        },
      )}
    >
      <Link
        href="/"
        className={cn(
          "text-alt flex items-center gap-6 rounded-xl border border-transparent p-4 text-5xl font-bold text-black transition-all duration-500",
          {
            "mt-2.5": !isMap,
            "bg-grey-500/50 border-white/70 text-white shadow shadow-white/50 backdrop-blur-sm text-shadow-2xs hover:mt-2.5":
              isMap,
          },
        )}
      >
        SafeSteps <Footprints size={40} />
      </Link>
    </div>
  );
}
