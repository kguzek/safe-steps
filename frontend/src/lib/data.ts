import NodeGeocoder from "node-geocoder";

import data from "@/../data.json";

import type { DangerZone } from "./types";

interface RawData {
  labels: {
    miejsce: string;
    data: string;
    szacowany_czas_zakonczenia: string;
    poziom_zagrozenia: number;
    komfort: number;
    podsumowanie: string;
    adres_url: string;
  };
}

const geocoder = NodeGeocoder({
  // @ts-expect-error idk
  fetch: globalThis.fetch.bind(globalThis),
  provider: "openstreetmap",
});

export async function parseData(): Promise<DangerZone[]> {
  const rawData = data as RawData[];

  return await Promise.all(
    rawData.map(async ({ labels }) => {
      const address = labels.miejsce
        .replace(" (oszacowano)", "")
        .replace(/\w+:\s?/, "")
        .replace("Intersection of", "")
        .replace(" and ", " & ");
      const result = await geocoder.geocode(address);
      const geo = result[0];

      if (geo == null) {
        throw new Error(`Could not geocode address: ${address}, result: ${result}`);
      }

      if (geo.latitude == null || geo.longitude == null) {
        throw new Error(`Could not geocode address: ${address}`);
      }

      const zone: DangerZone = {
        address: labels.miejsce,
        title: labels.podsumowanie,
        position: [geo.latitude, geo.longitude],
        date: new Date(labels.data),
        description: labels.podsumowanie,
        level:
          labels.poziom_zagrozenia <= 2
            ? "low"
            : labels.poziom_zagrozenia <= 4
              ? "medium"
              : "high",
        url: labels.adres_url,
      };
      return zone;
    }),
  );
}
