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
  // Track when map is ready to ensure heatmap layer is added after map initialization
  const [mapReady, setMapReady] = useState(false);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up existing map if it exists
    if (mapRef.current) {
      mapRef.current.remove();
      mapRef.current = null;
      setMapReady(false);
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
    // Signal that the map is ready for the heatmap layer
    setMapReady(true);

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        setMapReady(false);
      }
    };
  }, [center, zoom]);

  // Update heatmap layer when points change or map becomes ready
  useEffect(() => {
    if (!mapRef.current || !mapReady) return;

    // Remove existing heat layer
    if (heatLayerRef.current) {
      mapRef.current.removeLayer(heatLayerRef.current);
    }

    if (points.length === 0) {
      return;
    }

    // Calculate max count for normalization
    const maxCount = Math.max(...points.map((p) => p.count), 1);

    // Convert points to format expected by leaflet.heat
    // Format: [lat, lng, intensity]
    const heatPoints = points.map((point) => {
      // If all points have the same count (max_count = 1), give them a visible intensity
      // Otherwise, normalize based on count
      let intensity: number;
      if (maxCount === 1) {
        // All points have count 1, use a fixed visible intensity
        intensity = 0.4; // Medium intensity so it's visible
      } else {
        // Normalize count to 0-1 range with square root for better distribution
        intensity = Math.sqrt(point.count / maxCount);
        // Ensure minimum intensity for visibility
        intensity = Math.max(intensity, 0.2);
      }

      return [
        point.latitude,
        point.longitude,
        intensity,
      ];
    });

    // Create heat layer with custom options
    // @ts-ignore - heatLayer is added by leaflet.heat plugin
    const heatLayer = L.heatLayer(heatPoints, {
      radius: 40, // Increased radius for better visibility when points are sparse
      blur: 20, // Increased blur to make points blend together
      maxZoom: 17, // Maximum zoom level where heatmap is visible
      max: 1.0, // Maximum intensity (use full range)
      minOpacity: 0.4, // Increased minimum opacity for better visibility
      gradient: {
        // Color gradient from low to high intensity (more vibrant colors)
        0.0: "#0000FF", // Deep blue
        0.2: "#00BFFF", // Deep sky blue
        0.4: "#00FF00", // Lime green
        0.6: "#FFFF00", // Yellow
        0.8: "#FF6600", // Orange
        1.0: "#FF0000", // Red
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
  }, [points, mapReady]);

  return (
    <div
      ref={containerRef}
      className={`w-full rounded-xl overflow-hidden border border-border relative ${className}`}
      style={{ height, zIndex: 1 }}
    />
  );
}
