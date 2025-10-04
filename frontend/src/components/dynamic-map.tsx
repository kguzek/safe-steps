"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

import type { MapProps } from "@/components/map";

export function DynamicMap(props: MapProps) {
  const Map = useMemo(
    () =>
      dynamic(() => import("@/components/map").then((map) => map.Map), {
        loading: () => <p>Trwa ładowanie mapy...</p>,
        ssr: false,
      }),
    [],
  );
  return <Map {...props} />;
}
