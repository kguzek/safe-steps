import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Page() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-6">
      <h1 className="text-4xl font-bold">Witaj w Safe Steps!</h1>
      <p className="text-muted-foreground text-lg">
        Sprawdź bezpieczeństwo swojej okolicy
      </p>
      <Button asChild variant="link">
        <Link href="/map">Przejdź do mapy</Link>
      </Button>
    </div>
  );
}
