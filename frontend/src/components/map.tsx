"use client";

import { MapContainer, Marker, TileLayer, Tooltip } from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "leaflet-defaulticon-compatibility";
import "leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css";

import type { LatLngExpression } from "leaflet";
import Link from "next/link";
import { useState } from "react";
import { divIcon } from "leaflet";
import { MapPinned, Phone } from "lucide-react";

import type { DangerZone } from "@/lib/types";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { cn } from "@/lib/utils";

import { Button } from "./ui/button";

export interface MapProps {
  position: LatLngExpression;
  zoom: number;
  dangerZones?: DangerZone[];
}

function DangerMarker({ zone }: { zone: DangerZone }) {
  const [isOpen, setIsOpen] = useState(false);

  const icon = divIcon({
    className: cn(
      "rounded-full min-w-20 min-h-20 opacity-60 hover:opacity-100 transition-opacity duration-200 border-2",
      {
        "bg-yellow-500/80 border-yellow-500": zone.level === "low",
        "bg-orange-500/80 border-orange-500": zone.level === "medium",
        "bg-red-500/80 border-red-500": zone.level === "high",
      },
    ),
    iconAnchor: [0, 24],
    popupAnchor: [0, -36],
  });

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <Marker
        position={zone.position}
        icon={icon}
        eventHandlers={{
          click: () => {
            if (isOpen) {
              return;
            }
            setIsOpen(true);
          },
        }}
      >
        <Tooltip className="line-clamp-2">{zone.title}</Tooltip>
      </Marker>
      <SheetContent
        className={cn("z-[2000] my-10 h-[calc(100%-80px)] rounded-lg transition-all", {
          "mx-10": isOpen,
        })}
        side="left"
      >
        <SheetHeader>
          <SheetTitle>{zone.title}</SheetTitle>
          <SheetDescription>{zone.description}</SheetDescription>
        </SheetHeader>
        <div className="flex justify-center">
          <div className="flex flex-col items-stretch gap-5 px-4">
            <p>Lokalizacja: {zone.address}</p>
            <p>Data wydarzenia: {zone.date.toLocaleString()}</p>
            <Button asChild variant="link">
              <Link href={zone.url}>Więcej informacji</Link>
            </Button>
            <Button asChild>
              <Link
                href={`https://www.google.com/maps/dir/?api=1&destination=${zone.position.join(",")}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                <MapPinned /> Nawiguj
              </Link>
            </Button>

            <Button asChild>
              <Link href="tel:112">
                <Phone /> Wezwij pomoc
              </Link>
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export function Map({ position, zoom, dangerZones = [] }: MapProps) {
  return (
    <MapContainer center={position} zoom={zoom} className="h-screen w-screen">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {dangerZones.map((zone, index) => (
        <DangerMarker key={`map-marker-${index}`} zone={zone} />
      ))}
    </MapContainer>
  );
}
