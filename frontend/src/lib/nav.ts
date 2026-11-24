export type NavItem = { href: string; label: string; phase: number };

// `phase` indica en qué fase del plan la sección pasa a ser funcional.
export const NAV: NavItem[] = [
  { href: "/", label: "Dashboard", phase: 1 },
  { href: "/radar", label: "Radar viral", phase: 3 },
  { href: "/library", label: "Biblioteca", phase: 4 },
  { href: "/analysis", label: "Análisis", phase: 5 },
  { href: "/scripts", label: "Guiones", phase: 6 },
  { href: "/studio", label: "Estudio de producción", phase: 7 },
  { href: "/review", label: "Revisión de clips", phase: 8 },
  { href: "/exports", label: "Exportaciones", phase: 8 },
  { href: "/settings", label: "Configuración", phase: 1 },
];
