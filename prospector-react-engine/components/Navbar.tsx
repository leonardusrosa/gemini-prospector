import React from "react";
import { BUSINESS_INFO } from "@/lib/data";

export function Navbar() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 w-full bg-[#08090b]/90 backdrop-blur-md border-b border-white/[0.08]">
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 h-16 flex items-center justify-between">
        {/* Brand Wordmark */}
        <a
          href="#"
          className="flex items-center gap-3 text-xs sm:text-sm font-bold tracking-widest font-display uppercase text-white hover:text-[#caa35d] transition-colors"
        >
          <span className="w-1.5 h-1.5 bg-[#caa35d] inline-block" />
          <span>{BUSINESS_INFO.name}</span>
        </a>

        {/* Typographic Nav Links (Enhanced Legibility) */}
        <nav aria-label="Primary Navigation" className="hidden md:flex items-center gap-10 text-[13px] font-medium tracking-[0.14em] uppercase text-neutral-300">
          <a
            href="#services"
            className="hover:text-white transition-colors relative py-1 hover:after:w-full after:w-0 after:h-[1px] after:bg-[#caa35d] after:absolute after:bottom-0 after:left-0 after:transition-all"
          >
            Services
          </a>
          <a
            href="#comparison"
            className="hover:text-white transition-colors relative py-1 hover:after:w-full after:w-0 after:h-[1px] after:bg-[#caa35d] after:absolute after:bottom-0 after:left-0 after:transition-all"
          >
            Comparison
          </a>
          <a
            href="#reviews"
            className="hover:text-white transition-colors relative py-1 hover:after:w-full after:w-0 after:h-[1px] after:bg-[#caa35d] after:absolute after:bottom-0 after:left-0 after:transition-all"
          >
            Reviews
          </a>
          <a
            href="#gallery"
            className="hover:text-white transition-colors relative py-1 hover:after:w-full after:w-0 after:h-[1px] after:bg-[#caa35d] after:absolute after:bottom-0 after:left-0 after:transition-all"
          >
            Gallery
          </a>
          <a
            href="#studio"
            className="hover:text-white transition-colors relative py-1 hover:after:w-full after:w-0 after:h-[1px] after:bg-[#caa35d] after:absolute after:bottom-0 after:left-0 after:transition-all"
          >
            Studio
          </a>
        </nav>

        {/* Direct Action Link (Architectural Hairline) */}
        <a
          href={`tel:${BUSINESS_INFO.phone}`}
          className="text-xs sm:text-[13px] font-medium tracking-widest uppercase text-[#caa35d] hover:text-white transition-colors border-b border-[#caa35d]/50 hover:border-white pb-0.5"
        >
          {BUSINESS_INFO.phoneDisplay} →
        </a>
      </div>
    </header>
  );
}
