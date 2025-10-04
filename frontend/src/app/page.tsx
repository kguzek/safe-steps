import Link from "next/link";

import { DotGridBackground } from "@/components/dot-grid";
import { Button } from "@/components/ui/button";

export default function Page() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-6">
      <DotGridBackground />
      <h2 className="text-4xl font-bold">Witaj w SafeSteps!</h2>
      <p className="text-muted-foreground text-lg">
        Sprawdź bezpieczeństwo swojej okolicy
      </p>
      <Button asChild variant="link">
        <Link href="/map">Przejdź do mapy</Link>
      </Button>
    </div>
  );
}
