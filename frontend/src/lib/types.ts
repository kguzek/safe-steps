import type { LatLngExpression } from "leaflet";

export type DangerLevel = "low" | "medium" | "high";

interface DangerZoneWithoutPosition {
  address?: string;
  title: string;
  description: string;
  level: DangerLevel;
}

export interface DangerZone extends DangerZoneWithoutPosition {
  position: [number, number];
}
