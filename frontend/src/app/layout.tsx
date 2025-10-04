import type { Metadata } from "next";
import { Henny_Penny, Space_Grotesk } from "next/font/google";

import { QueryProvider } from "@/lib/query-client";

import "./globals.css";

import { Heading } from "@/components/heading";
import { cn } from "@/lib/utils";

const space_grotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

const henny_penny = Henny_Penny({
  variable: "--font-henny-penny",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: "Safe Steps",
  description: "Check the safety of your surroundings",
  icons: "/safe-steps.png",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <QueryProvider>
        <body
          className={cn(
            "font-sans antialiased",
            space_grotesk.variable,
            henny_penny.variable,
          )}
        >
          <Heading />
          {children}
        </body>
      </QueryProvider>
    </html>
  );
}
