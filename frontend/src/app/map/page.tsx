import type { DangerZone } from "@/lib/types";
import { DynamicMap } from "@/components/dynamic-map";

const dangerZones: DangerZone[] = [
  {
    position: [48.858345547135826, 2.2943582487893157],
    title: "Ktoś kogoś okradł na ul. Żabojadzkiej",
    description: "Zgłoszono kradzież na ul. Żabojadzkiej. Bądź ostrożny.",
    level: "high",
  },
  {
    position: [48.853, 2.3499],
    title: "Zgłoszono podejrzaną aktywność",
    description: "Zgłoszono podejrzaną aktywność w okolicy. Zachowaj ostrożność.",
    level: "medium",
  },
  {
    position: [48.8566, 2.3522],
    title: "Niedawno miała miejsce bójka",
    description: "Niedawno miała miejsce bójka. Unikaj tego obszaru, jeśli to możliwe.",
    level: "low",
  },
  {
    position: [48.8606, 2.3376],
    title: "Obszar o podwyższonym ryzyku kradzieży",
    description: "Ten obszar ma historię kradzieży. Bądź czujny.",
    level: "medium",
  },
];

export default function Home() {
  return (
    <>
      <DynamicMap
        position={[48.858345547135826, 2.2943582487893157]}
        zoom={12}
        dangerZones={dangerZones}
      />
      <div className="absolute top-10 flex w-screen justify-center">
        <div className="text-alt z-[3000] text-6xl font-bold text-blue-500 text-shadow-2xs text-shadow-black/50">
          {/* SafeSteps */}
        </div>
      </div>
    </>
  );
}
