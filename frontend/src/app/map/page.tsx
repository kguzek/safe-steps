import { DynamicMap } from "@/components/dynamic-map";
import { parseData } from "@/lib/data";

export default async function Home() {
  const dangerZones = await parseData();
  return (
    <DynamicMap
      position={[51.4993956698114, -0.11198360223097771]}
      zoom={12}
      dangerZones={dangerZones}
    />
  );
}
