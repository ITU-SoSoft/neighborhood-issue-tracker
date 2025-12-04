"use client";

import { useEffect, useState, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in Leaflet with Next.js
const defaultIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = defaultIcon;

interface LocationPickerProps {
  initialPosition?: { lat: number; lng: number };
  onLocationSelect: (location: {
    latitude: number;
    longitude: number;
    address?: string;
  }) => void;
  className?: string;
}

export function LocationPicker({
  initialPosition,
  onLocationSelect,
  className = "",
}: LocationPickerProps) {
  const mapRef = useRef<L.Map | null>(null);
  const markerRef = useRef<L.Marker | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLocating, setIsLocating] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(
    initialPosition || null
  );

  // Default to Istanbul if no location provided
  const defaultCenter = { lat: 41.0082, lng: 28.9784 };

  useEffect(() => {
    // Request user's current location
    if (!initialPosition && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lng: longitude });
          setIsLoading(false);
        },
        () => {
          // Failed to get location, use default
          setUserLocation(defaultCenter);
          setIsLoading(false);
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      );
    } else {
      setUserLocation(initialPosition || defaultCenter);
      setIsLoading(false);
    }
  }, [initialPosition]);

  useEffect(() => {
    if (!containerRef.current || !userLocation || mapRef.current) return;

    // Initialize map
    const map = L.map(containerRef.current).setView(
      [userLocation.lat, userLocation.lng],
      15
    );

    // Add tile layer (OpenStreetMap)
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    // Add initial marker (not draggable - click to set location instead)
    const marker = L.marker([userLocation.lat, userLocation.lng], {
      draggable: false,
    }).addTo(map);

    // Handle map click to move marker
    map.on("click", (e: L.LeafletMouseEvent) => {
      marker.setLatLng(e.latlng);
      reverseGeocode(e.latlng.lat, e.latlng.lng);
    });

    mapRef.current = map;
    markerRef.current = marker;

    // Fix rendering issues - invalidate size after map is added to DOM
    setTimeout(() => {
      map.invalidateSize();
    }, 100);

    // Initial location callback
    reverseGeocode(userLocation.lat, userLocation.lng);

    return () => {
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, [userLocation]);

  // Handle container resize
  useEffect(() => {
    if (!mapRef.current) return;

    const resizeObserver = new ResizeObserver(() => {
      mapRef.current?.invalidateSize();
    });

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, [userLocation]);

  const reverseGeocode = async (lat: number, lng: number) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`,
        {
          headers: {
            "Accept-Language": "en",
          },
        }
      );
      const data = await response.json();
      
      onLocationSelect({
        latitude: lat,
        longitude: lng,
        address: data.display_name || undefined,
      });
    } catch {
      onLocationSelect({
        latitude: lat,
        longitude: lng,
      });
    }
  };

  const getGeolocationErrorMessage = (error: GeolocationPositionError): string => {
    switch (error.code) {
      case error.PERMISSION_DENIED:
        return "Location access denied. Please enable location permissions in your browser settings.";
      case error.POSITION_UNAVAILABLE:
        return "Location information is unavailable.";
      case error.TIMEOUT:
        return "Location request timed out.";
      default:
        return "An unknown error occurred while getting your location.";
    }
  };

  const handleLocateMe = () => {
    if (navigator.geolocation) {
      setLocationError(null);
      setIsLocating(true);
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          if (mapRef.current && markerRef.current) {
            mapRef.current.setView([latitude, longitude], 15);
            markerRef.current.setLatLng([latitude, longitude]);
            reverseGeocode(latitude, longitude);
          }
          setIsLocating(false);
        },
        (error) => {
          setLocationError(getGeolocationErrorMessage(error));
          setIsLocating(false);
          // Auto-dismiss error after 5 seconds
          setTimeout(() => setLocationError(null), 5000);
        }
      );
    }
  };

  if (isLoading) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-100 rounded-xl ${className}`}
        style={{ minHeight: "300px" }}
      >
        <div className="text-center text-slate-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-2" />
          <p className="text-sm">Getting your location...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      <div
        ref={containerRef}
        className="w-full rounded-xl overflow-hidden"
        style={{ height: "300px" }}
      />
      
      {/* Help text overlay - top center */}
      <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] bg-black/70 backdrop-blur-sm text-white text-xs px-3 py-1.5 rounded-full pointer-events-none">
        Click to set location
      </div>

      {/* My Location button - top right, icon-only with tooltip */}
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          handleLocateMe();
        }}
        disabled={isLocating}
        title="Use my current location"
        className="absolute top-3 right-3 z-[1000] bg-white rounded-lg p-2.5 shadow-md hover:bg-slate-50 hover:shadow-lg active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
      >
        {isLocating ? (
          <div className="w-5 h-5 border-2 border-slate-300 border-t-emerald-600 rounded-full animate-spin" />
        ) : (
          <svg
            className="w-5 h-5 text-slate-700 group-hover:text-emerald-600 transition-colors"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <circle cx="12" cy="12" r="3" />
            <path d="M12 2v3m0 14v3m10-10h-3M5 12H2" />
          </svg>
        )}
      </button>

      {/* Error toast - bottom center, inside map */}
      {locationError && (
        <div className="absolute bottom-3 left-3 right-3 z-[1000] bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-2 animate-in slide-in-from-bottom-2 duration-200">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <circle cx="12" cy="12" r="10" />
            <path d="M12 8v4m0 4h.01" />
          </svg>
          <span className="flex-1">{locationError}</span>
          <button 
            onClick={() => setLocationError(null)}
            className="p-1 hover:bg-red-100 rounded transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
