import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { GeoPoint, GridStation } from '../types';

interface InteractiveMapProps {
  selectedLocation: GeoPoint;
  onSelectLocation: (loc: GeoPoint) => void;
  stations?: GridStation[];
  compareLocation?: GeoPoint;
  onSelectCompareLocation?: (loc: GeoPoint) => void;
  isCompareMode?: boolean;
}

export const InteractiveMap: React.FC<InteractiveMapProps> = ({
  selectedLocation,
  onSelectLocation,
  stations = [],
  compareLocation,
  onSelectCompareLocation,
  isCompareMode = false,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Initialize Leaflet Map centered on Egypt (Cairo)
    const map = L.map(mapContainerRef.current, {
      center: [selectedLocation.latitude || 30.0444, selectedLocation.longitude || 31.2357],
      zoom: 7,
      minZoom: 3,
      maxZoom: 14,
    });

    // Dark Matter tile layer for premium scientific aesthetic
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    const markersGroup = L.layerGroup().addTo(map);
    markersLayerRef.current = markersGroup;
    mapInstanceRef.current = map;

    // Click on map to select custom location
    map.on('click', (e: L.LeafletMouseEvent) => {
      const { lat, lng } = e.latlng;
      const point: GeoPoint = {
        latitude: parseFloat(lat.toFixed(4)),
        longitude: parseFloat(lng.toFixed(4)),
        name: `Coordinate (${lat.toFixed(3)}°N, ${lng.toFixed(3)}°E)`,
      };
      if (isCompareMode && onSelectCompareLocation) {
        onSelectCompareLocation(point);
      } else {
        onSelectLocation(point);
      }
    });

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update markers whenever selectedLocation, compareLocation, or stations change
  useEffect(() => {
    if (!mapInstanceRef.current || !markersLayerRef.current) return;
    const markers = markersLayerRef.current;
    markers.clearLayers();

    // 1. Render NASA Verified Grid Stations
    stations.forEach((st) => {
      const isSelected = Math.abs(st.latitude - selectedLocation.latitude) < 0.1 && Math.abs(st.longitude - selectedLocation.longitude) < 0.1;
      const isCompare = compareLocation && Math.abs(st.latitude - compareLocation.latitude) < 0.1 && Math.abs(st.longitude - compareLocation.longitude) < 0.1;

      const markerColor = isSelected ? '#10b981' : isCompare ? '#38bdf8' : '#059669';
      const radius = isSelected || isCompare ? 9 : 6;

      const circle = L.circleMarker([st.latitude, st.longitude], {
        radius,
        fillColor: markerColor,
        color: '#ffffff',
        weight: isSelected || isCompare ? 2.5 : 1,
        opacity: 0.9,
        fillOpacity: isSelected || isCompare ? 0.9 : 0.6,
      });

      circle.bindTooltip(`<b>${st.name}</b><br><span style="color:#10b981;">Verified NASA POWER Grid</span><br>${st.latitude}°N, ${st.longitude}°E`, {
        direction: 'top',
        className: 'leaflet-popup-content-wrapper',
      });

      circle.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        const pt: GeoPoint = {
          latitude: st.latitude,
          longitude: st.longitude,
          name: st.name,
        };
        if (isCompareMode && onSelectCompareLocation) {
          onSelectCompareLocation(pt);
        } else {
          onSelectLocation(pt);
        }
      });

      circle.addTo(markers);
    });

    // 2. Render Target Selection Marker
    if (selectedLocation) {
      const primaryIcon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background-color:#10b981; width:16px; height:16px; border-radius:50%; border:3px solid #ffffff; box-shadow:0 0 15px #10b981;"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });
      L.marker([selectedLocation.latitude, selectedLocation.longitude], { icon: primaryIcon })
        .bindPopup(`<b>Primary Location (A)</b><br>${selectedLocation.name || 'Selected Point'}<br>${selectedLocation.latitude.toFixed(4)}°N, ${selectedLocation.longitude.toFixed(4)}°E`)
        .addTo(markers);
    }

    // 3. Render Compare Selection Marker
    if (compareLocation) {
      const compareIcon = L.divIcon({
        className: 'custom-pin',
        html: `<div style="background-color:#38bdf8; width:16px; height:16px; border-radius:50%; border:3px solid #ffffff; box-shadow:0 0 15px #38bdf8;"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8],
      });
      L.marker([compareLocation.latitude, compareLocation.longitude], { icon: compareIcon })
        .bindPopup(`<b>Compare Location (B)</b><br>${compareLocation.name || 'Compare Point'}<br>${compareLocation.latitude.toFixed(4)}°N, ${compareLocation.longitude.toFixed(4)}°E`)
        .addTo(markers);
    }
  }, [selectedLocation, compareLocation, stations, isCompareMode]);

  return (
    <div className="relative w-full h-[420px] rounded-2xl overflow-hidden border border-slate-800 shadow-xl">
      <div ref={mapContainerRef} className="w-full h-full" />
      
      {/* Map Legend Overlay */}
      <div className="absolute bottom-3 left-3 z-[1000] glass-panel px-3 py-2 rounded-lg text-xs flex flex-wrap items-center gap-4 border border-slate-700/60 bg-navy-950/85">
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full bg-emerald-500 border border-white inline-block"></span>
          <span className="text-slate-300 font-medium">Selected (A)</span>
        </div>
        {isCompareMode && (
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-400 border border-white inline-block"></span>
            <span className="text-slate-300 font-medium">Compare (B)</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-600/70 border border-emerald-400 inline-block"></span>
          <span className="text-slate-400">30 Verified NASA Grid Points</span>
        </div>
      </div>
    </div>
  );
};
