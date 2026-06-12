(() => {
  function isPwaDisplayMode() {
    return (
      window.matchMedia?.("(display-mode: standalone)")?.matches ||
      window.matchMedia?.("(display-mode: fullscreen)")?.matches ||
      window.navigator.standalone === true ||
      document.referrer.startsWith("android-app://")
    );
  }

  function enforceNoZoomInPwa() {
    if (!isPwaDisplayMode()) return;

    const viewport = document.querySelector('meta[name="viewport"]');
    if (viewport) {
      viewport.setAttribute(
        "content",
        "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover"
      );
    }

    const prevent = (event) => event.preventDefault();

    // iOS Safari PWA gestures
    document.addEventListener("gesturestart", prevent, { passive: false });
    document.addEventListener("gesturechange", prevent, { passive: false });
    document.addEventListener("gestureend", prevent, { passive: false });

    // Android/Chrome pinch zoom fallback
    document.addEventListener(
      "touchmove",
      (event) => {
        if (event.touches && event.touches.length > 1) {
          event.preventDefault();
        }
      },
      { passive: false }
    );

    let lastTouchEnd = 0;
    document.addEventListener(
      "touchend",
      (event) => {
        const now = Date.now();
        if (now - lastTouchEnd <= 300) {
          event.preventDefault();
        }
        lastTouchEnd = now;
      },
      { passive: false }
    );
  }

  function extractRouteCode(routeName, routeSlug) {
    const nameMatch = (routeName || "").match(/(\d+)/);
    if (nameMatch) return nameMatch[1];

    const slugMatch = (routeSlug || "").match(/(\d+)/);
    if (slugMatch) return slugMatch[1];

    return null;
  }

  async function applyRouteBranding() {
    try {
      const response = await fetch("/api/route_context");
      if (!response.ok) return;

      const data = await response.json();
      const routeCode = extractRouteCode(data?.route_name, data?.route_slug);
      if (!routeCode) return;

      document.title = document.title.replace(/PéléVTT\s*\d+/i, `PéléVTT ${routeCode}`);
    } catch (_error) {
      // Rester silencieux: le branding ne doit pas bloquer l'UI.
    }
  }

  enforceNoZoomInPwa();

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyRouteBranding);
  } else {
    applyRouteBranding();
  }
})();