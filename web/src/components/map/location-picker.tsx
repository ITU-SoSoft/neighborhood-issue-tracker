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
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showResults, setShowResults] = useState(false);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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

  const searchAddress = async (query: string) => {
    if (!query.trim() || query.length < 3) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      // Add Istanbul context to search and use viewbox to prioritize Istanbul area
      // Istanbul approximate bounds: 40.8-41.3 lat, 28.5-29.4 lng
      const searchQuery = `${query}, Istanbul, Turkey`;
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?` +
        `format=json` +
        `&q=${encodeURIComponent(searchQuery)}` +
        `&limit=10` +
        `&addressdetails=1` +
        `&viewbox=28.5,41.3,29.4,40.8` + // Istanbul bounds (left,top,right,bottom)
        `&bounded=0` + // Allow results outside viewbox but prioritize inside
        `&accept-language=tr,en`, // Prefer Turkish, fallback to English
        {
          headers: {
            "User-Agent": "NeighborhoodIssueTracker/1.0",
          },
        }
      );
      const data = await response.json();
      
      // Filter and prioritize Istanbul results
      const filteredResults = data.filter((result: any) => {
        // Check if result is in Istanbul
        const address = result.address || {};
        return (
          address.city === "Istanbul" ||
          address.city === "İstanbul" ||
          address.state === "Istanbul" ||
          address.state === "İstanbul" ||
          result.display_name.toLowerCase().includes("istanbul") ||
          result.display_name.toLowerCase().includes("İstanbul")
        );
      });

      setSearchResults(filteredResults.length > 0 ? filteredResults : data);
      setShowResults(true);
    } catch (error) {
      console.error("Address search failed:", error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    
    // Clear existing timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce search
    searchTimeoutRef.current = setTimeout(() => {
      searchAddress(value);
    }, 500);
  };

  const handleSelectResult = (result: any) => {
    const lat = parseFloat(result.lat);
    const lng = parseFloat(result.lon);

    if (mapRef.current && markerRef.current) {
      // Smooth zoom to location
      mapRef.current.flyTo([lat, lng], 17, {
        duration: 1.5,
      });
      markerRef.current.setLatLng([lat, lng]);
      
      // Add a pulse effect by temporarily adding a circle
      const circle = L.circle([lat, lng], {
        color: '#3b82f6',
        fillColor: '#3b82f6',
        fillOpacity: 0.3,
        radius: 50,
      }).addTo(mapRef.current);
      
      setTimeout(() => {
        circle.remove();
      }, 2000);
      
      reverseGeocode(lat, lng);
    }

    setSearchQuery("");
    setShowResults(false);
    setSearchResults([]);
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
    <div className={`relative ${className} space-y-3`}>
      {/* Search input */}
      <div className="relative z-[1100]">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search address (street, neighborhood, district)..."
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            onFocus={() => setShowResults(searchResults.length > 0)}
            className="w-full pl-10 pr-10 py-2.5 border border-border rounded-lg bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent relative z-10"
          />
          {isSearching && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 z-20">
              <div className="w-4 h-4 border-2 border-muted-foreground/20 border-t-primary rounded-full animate-spin" />
            </div>
          )}
        </div>

        {/* Search results dropdown */}
        {showResults && searchResults.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-background border border-border rounded-lg shadow-xl z-[1200] max-h-96 overflow-y-auto">
            {searchResults.map((result, index) => {
              const address = result.address || {};
              const mainName = address.road || address.suburb || address.neighbourhood || address.district || result.name || "Unknown";
              const district = address.district || address.suburb || "";
              const city = address.city || address.state || "";
              
              return (
                <button
                  key={`${result.place_id}-${index}`}
                  type="button"
                  onClick={() => handleSelectResult(result)}
                  className="w-full text-left px-4 py-3 hover:bg-muted transition-colors border-b border-border last:border-b-0 flex items-start gap-3"
                >
                  <svg
                    className="w-5 h-5 text-primary shrink-0 mt-0.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-foreground">
                      {mainName}
                    </p>
                    {(district || city) && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {[district, city].filter(Boolean).join(", ")}
                      </p>
                    )}
                    {result.type && (
                      <p className="text-xs text-primary/60 mt-0.5 capitalize">
                        {result.type.replace("_", " ")}
                      </p>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {/* No results message */}
        {showResults && searchResults.length === 0 && !isSearching && searchQuery.length >= 3 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-background border border-border rounded-lg shadow-xl z-[1200] p-4 text-center">
            <p className="text-sm text-muted-foreground">No addresses found</p>
            <p className="text-xs text-muted-foreground mt-1">Try searching with street name, neighborhood, or district</p>
          </div>
        )}
      </div>

      {/* Map container */}
      <div className="relative">
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

      {/* Click outside to close results */}
      {showResults && (
        <div
          className="fixed inset-0 z-[1050]"
          onClick={() => setShowResults(false)}
        />
      )}
    </div>
  );
}
