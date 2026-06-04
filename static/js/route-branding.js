(() => {
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

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", applyRouteBranding);
  } else {
    applyRouteBranding();
  }
})();