export type DangerLevel = "low" | "medium" | "high";

export interface DangerZone {
  address?: string;
  title: string;
  description: string;
  level: DangerLevel;
  date: Date;
  position: [number, number];
  url: string;
}
