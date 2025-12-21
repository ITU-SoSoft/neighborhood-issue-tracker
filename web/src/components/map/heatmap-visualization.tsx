"use client";

import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
// @ts-ignore - leaflet.heat doesn't have perfect type definitions
import "leaflet.heat";

interface HeatmapPoint {
  latitude: number;
  longitude: number;
  count: number;
  intensity: number;
}

interface HeatmapVisualizationProps {
  points: HeatmapPoint[];
  className?: string;
  height?: string;
  center?: [number, number];
  zoom?: number;
}

export function HeatmapVisualization({
  points,
  className = "",
  height = "400px",
  center = [41.0082, 28.9784], // Default to Istanbul
  zoom = 11,
}: HeatmapVisualizationProps) {
  const mapRef = useRef<L.Map | null>(null);
  const heatLayerRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up existing map if it exists
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
    }

    // Initialize map
    const map = L.map(containerRef.current, {
      scrollWheelZoom: true,
      dragging: true,
      zoomControl: true,
    }).setView(center, zoom);

    // Add tile layer (OpenStreetMap)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 18,
    }).addTo(map);

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [center, zoom]);

  // Update heatmap layer when points change
  useEffect(() => {
    if (!mapRef.current) return;

    // Remove existing heat layer
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
    }

    if (points.length === 0) {
      return;
    }

    // Convert points to format expected by leaflet.heat
    // Format: [lat, lng, intensity]
    const heatPoints = points.map((point) => [
      point.latitude,
      point.longitude,
      point.intensity, // Use intensity (0-1) for better visualization
    ]);

    // Create heat layer with custom options
    // @ts-ignore - heatLayer is added by leaflet.heat plugin
    const heatLayer = L.heatLayer(heatPoints, {
      radius: 25, // Radius of each point in pixels
      blur: 15, // Amount of blur
      maxZoom: 17, // Maximum zoom level where heatmap is visible
      max: 1.0, // Maximum intensity (we use normalized intensity)
      gradient: {
        // Color gradient from low to high intensity
        0.0: "blue",
        0.2: "cyan",
        0.4: "lime",
        0.6: "yellow",
        0.8: "orange",
        1.0: "red",
      },
    });

    heatLayer.addTo(mapRef.current);
    heatLayerRef.current = heatLayer;

    // Auto-fit map bounds to show all points
    if (points.length > 0) {
      const bounds = L.latLngBounds(
        points.map((p) => [p.latitude, p.longitude] as [number, number])
      );
      mapRef.current.fitBounds(bounds, {
        padding: [50, 50],
        maxZoom: 13,
      });
    }
  }, [points]);

  return (
    <div
      ref={containerRef}
      className={`w-full rounded-xl overflow-hidden border border-border ${className}`}
      style={{ height }}
    />
  );
}
