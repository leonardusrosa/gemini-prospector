import React from "react";
import { BUSINESS_INFO } from "@/lib/data";

export function Footer() {
  return (
    <footer className="w-full py-14 border-t border-white/10 bg-[#08090b] text-neutral-300 text-sm overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 flex flex-col sm:flex-row items-center justify-between gap-6 opacity-100 transition-opacity duration-700">
        <div>
          <span className="font-semibold text-white font-display tracking-wider uppercase">
            {BUSINESS_INFO.name}
          </span>
          <span className="mx-3 text-neutral-600">|</span>
          <span className="text-neutral-400">© {new Date().getFullYear()} All rights reserved.</span>
        </div>

        <div className="flex items-center gap-6 text-sm text-neutral-400">
          <span>{BUSINESS_INFO.address.split(",")[0]} • {BUSINESS_INFO.cityState}</span>
          <span className="hidden sm:inline text-neutral-600">•</span>
          <span className="hidden sm:inline text-[#caa35d] font-semibold">
            ★ {BUSINESS_INFO.rating} Rating ({BUSINESS_INFO.reviewCount} Reviews)
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-neutral-500">
          <span data-social="whatsapp" aria-disabled="true">WhatsApp unavailable</span>
          <span data-social="instagram" aria-disabled="true">Instagram unverified</span>
        </div>

        <div>
          <a
            href="#"
            className="hover:text-white uppercase tracking-widest text-xs transition-colors text-neutral-400 font-mono"
          >
            Back to Top ↑
          </a>
        </div>
      </div>
    </footer>
  );
}
