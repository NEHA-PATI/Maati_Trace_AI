import { useCallback, useState } from "react";
import { MAP_CONFIG } from "@/lib/mapConfig";

export default function useDeviceLocation() {
  const [location, setLocation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const locate = useCallback(() => {
    if (!navigator.geolocation) { setError("This device does not support location."); return; }
    setLoading(true); setError("");
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLocation({ latitude: coords.latitude, longitude: coords.longitude, accuracy: coords.accuracy, precision: "gps" });
        if (coords.accuracy > MAP_CONFIG.maximumGpsAccuracy) {
          setError(`GPS accuracy is approximately ±${Math.round(coords.accuracy)} metres. Check the satellite image carefully.`);
        }
        setLoading(false);
      },
      (gpsError) => {
        if (gpsError.code === gpsError.PERMISSION_DENIED) setError("Location permission was denied. Allow location access or find the farm manually.");
        else if (gpsError.code === gpsError.TIMEOUT) setError("Location detection timed out. Move outdoors and try again.");
        else setError("Your current location could not be detected.");
        setLoading(false);
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 15000 },
    );
  }, []);

  return { location, loading, error, locate };
}
