"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type MouseEvent } from "react";

const NAV_ITEMS = [
  { href: "/#top", label: "Overview" },
  { href: "/#q1", label: "The Case" },
  { href: "/#q4", label: "Compare" },
  { href: "/#q5", label: "H.O.M.E." },
  { href: "/#close", label: "Solutions" },
  { href: "/data/", label: "Data" },
  { href: "/memo/", label: "Memo" },
];

export const SiteHeader = () => {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  // Next's <Link href="/#q1"> doesn't scroll to the fragment when already on "/".
  // On the home page, intercept hash links and scroll the target into view ourselves
  // (scroll-padding-top in globals.css handles the sticky-header offset).
  const handleHashNav = (href: string) => (e: MouseEvent<HTMLAnchorElement>) => {
    setMenuOpen(false);
    const hashIdx = href.indexOf("#");
    if (hashIdx === -1 || pathname !== "/") return;
    const id = href.slice(hashIdx + 1);
    const el = document.getElementById(id);
    if (el) {
      e.preventDefault();
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      window.history.replaceState(null, "", `#${id}`);
    }
  };

  return (
    <header className="print:hidden sticky top-0 z-50 bg-white border-b-2 border-bpn-green shadow-sm">
      <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-16">
        <Link href="/" className="flex items-center gap-2">
          <img
            src="/images/bpn-icon-green.png"
            alt="Build Philly Now"
            className="h-9"
          />
          <span className="hidden sm:inline font-(family-name:--font-display) font-bold text-sm text-gray-800">
            MIN Impact Analysis
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleHashNav(item.href)}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-bpn-green text-white"
                    : "text-gray-700 hover:bg-bpn-cream"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Mobile hamburger */}
        <button
          className="lg:hidden p-2"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {menuOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {menuOpen && (
        <nav className="lg:hidden border-t border-gray-200 bg-white">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleHashNav(item.href)}
                className={`block px-4 py-3 text-sm font-medium border-b border-gray-100 ${
                  isActive ? "bg-bpn-green/10 text-bpn-green" : "text-gray-700"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      )}
    </header>
  );
};
