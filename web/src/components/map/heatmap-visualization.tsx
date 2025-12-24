"use client";

import { useEffect, useRef, useState } from "react";
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
  const [isMapInitialized, setIsMapInitialized] = useState(false);

  // Initialize map once on mount
  useEffect(() => {
    // Skip if no container or map already exists
    if (!containerRef.current || mapRef.current) {
      return;
    }

    // Create the map
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
    setIsMapInitialized(true);

    // Cleanup on unmount
    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
      setIsMapInitialized(false);
    };
  }, []); // Empty dependency - only run on mount

  // Update center/zoom when props change
  useEffect(() => {
    if (mapRef.current && isMapInitialized) {
      mapRef.current.setView(center, zoom);
    }
  }, [center, zoom, isMapInitialized]);

  // Update heatmap layer when points change
  useEffect(() => {
    if (!mapRef.current || !isMapInitialized) {
      return;
    }

    // Remove existing heat layer
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }

    // If no points, just show the map without heatmap
    if (points.length === 0) {
      return;
    }

    // Calculate max count for normalization
    const maxCount = Math.max(...points.map((p) => p.count), 1);

    // Convert points to format expected by leaflet.heat
    // Format: [lat, lng, intensity]
    const heatPoints = points.map((point) => {
      let intensity: number;
      if (maxCount === 1) {
        // All points have count 1, use a fixed visible intensity
        intensity = 0.4;
      } else {
        // Normalize count to 0-1 range with square root for better distribution
        intensity = Math.sqrt(point.count / maxCount);
        intensity = Math.max(intensity, 0.2);
      }

      return [point.latitude, point.longitude, intensity];
    });

    // Create heat layer with custom options
    // @ts-ignore - heatLayer is added by leaflet.heat plugin
    const heatLayer = L.heatLayer(heatPoints, {
      radius: 40,
      blur: 20,
      maxZoom: 17,
      max: 1.0,
      minOpacity: 0.4,
      gradient: {
        0.0: "#0000FF",
        0.2: "#00BFFF",
        0.4: "#00FF00",
        0.6: "#FFFF00",
        0.8: "#FF6600",
        1.0: "#FF0000",
      },
    });

    heatLayer.addTo(mapRef.current);
    heatLayerRef.current = heatLayer;

    // Auto-fit map bounds to show all points
    const bounds = L.latLngBounds(
      points.map((p) => [p.latitude, p.longitude] as [number, number])
    );
    mapRef.current.fitBounds(bounds, {
      padding: [50, 50],
      maxZoom: 13,
    });
  }, [points, isMapInitialized]);

  return (
    <div
      ref={containerRef}
      className={`w-full rounded-xl overflow-hidden border border-border relative ${className}`}
      style={{ height, zIndex: 1 }}
    />
  );
}
