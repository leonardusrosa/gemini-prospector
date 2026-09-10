import React from "react";
import { BUSINESS_INFO } from "@/lib/data";

export function Hero() {
  return (
    <section
      data-role="hero"
      className="relative w-full min-h-[92svh] md:min-h-[96svh] flex items-end justify-start overflow-hidden bg-[#08090b] pt-20"
    >
      {/* Background Media Plane: Full Bleed Authentic Static Poster (Zero Fake Motion / Zero Ken Burns) */}
      <div
        data-role="hero-media-plane"
        className="absolute inset-0 w-full h-full pointer-events-none z-0 overflow-hidden"
      >
        <img
          src="/assets/hero-poster.webp"
          alt="Precision automotive detailing studio environment in Addison Texas"
          fetchPriority="high"
          decoding="async"
          className="absolute inset-0 w-full h-full object-cover object-[72%_center] md:object-center opacity-100 scale-100"
        />

        {/* Independent Architectural Overlay (Copy Contrast on Left, Grounding on Bottom) */}
        <div className="absolute inset-y-0 left-0 w-full md:w-3/5 bg-gradient-to-r from-[#08090b] via-[#08090b]/85 to-transparent pointer-events-none" />
        <div className="absolute bottom-0 inset-x-0 h-44 bg-gradient-to-t from-[#08090b] via-[#08090b]/60 to-transparent pointer-events-none" />
      </div>

      {/* Hero Content Stage */}
      <div className="relative z-10 w-full max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 pt-24 pb-16 md:pb-24">
        <div className="max-w-3xl">
          {/* Factual Eyebrow */}
          <div className="animate-hero-eyebrow inline-flex items-center gap-3 mb-6" data-role="hero-eyebrow">
            <span className="text-xs uppercase tracking-[0.25em] font-semibold text-[#caa35d]">
              AUTO DETAILING • ADDISON, TEXAS
            </span>
            <div className="h-[1px] w-8 bg-[#caa35d]/40" />
          </div>

          {/* Master Headline: Line-by-Line Mask Clip Reveal */}
          <div className="overflow-hidden pb-1">
            <h1 className="animate-hero-headline text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight font-display uppercase leading-[1.08] text-white">
              AUTOMOTIVE DETAILING & PAINT REFINEMENT
            </h1>
          </div>

          {/* Factual Supporting Copy (Single concise sentence, zero duplication) */}
          <p
            data-role="hero-desc"
            className="animate-hero-desc hero-desc mt-6 text-base sm:text-lg text-neutral-300 font-light leading-relaxed max-w-2xl"
          >
            Auto detailing, paint correction, and buffing.
          </p>

          {/* Call to Action & Typographic Trust Strip */}
          <div className="animate-hero-cta mt-10 flex flex-col sm:flex-row items-start sm:items-center gap-8">
            <a
              href={`tel:${BUSINESS_INFO.phone}`}
              data-role="hero-cta"
              className="inline-flex items-center justify-center gap-4 px-8 py-4 bg-[#caa35d] text-black font-bold text-xs tracking-[0.15em] uppercase hover:bg-[#dcba78] transition-all transform active:scale-95 shadow-xl group rounded-sm"
            >
              <span>Call {BUSINESS_INFO.phoneDisplay}</span>
              <span className="transform transition-transform group-hover:translate-x-1">→</span>
            </a>

            {/* Compact Editorial Trust Line (Single-line, source neutral) */}
            <div
              data-role="hero-trust"
              className="flex items-center gap-2 text-sm text-neutral-300 font-display"
            >
              <span className="font-semibold text-white tracking-wide">
                ★ {BUSINESS_INFO.rating}
              </span>
              <span className="text-neutral-500 mx-1">/</span>
              <span className="text-neutral-300">
                {BUSINESS_INFO.reviewCount} Reviews
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
