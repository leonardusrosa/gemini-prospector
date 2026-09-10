"use client";

import React from "react";
import { GALLERY_MEDIA } from "@/lib/data";
import { useGalleryRail } from "./useGalleryRail";

export function GallerySection() {
  const {
    activeIdx,
    handlePrev,
    handleNext,
    railProps,
  } = useGalleryRail({
    total: GALLERY_MEDIA.length,
    intervalMs: 6500,
    idleResumeMs: 8000,
  });

  const currentItem = GALLERY_MEDIA[activeIdx];

  return (
    <section
      id="gallery"
      className="w-full py-24 md:py-32 bg-[#0a0c10] text-white border-t border-white/[0.06] overflow-hidden select-none"
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16">
        {/* Section Header with Minimal Stepper Controls */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12 md:mb-16">
          <div>
            <div className="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[#caa35d] mb-4">
              <span>[ 04 — WORKSHOP ARCHIVE ]</span>
              <div className="h-[1px] w-6 bg-[#caa35d]/40" />
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-display uppercase tracking-tight leading-tight">
              STUDIO & VEHICLE ARCHIVE
            </h2>
          </div>

          {/* Hairline Counter + Minimal Arrow Controls */}
          <div className="flex items-center gap-5 self-start md:self-end">
            <div className="font-mono text-xs text-neutral-400 tracking-wider">
              <span className="text-[#caa35d] font-semibold">
                {String(activeIdx + 1).padStart(2, "0")}
              </span>
              <span className="text-neutral-600">{" / "}</span>
              <span>{String(GALLERY_MEDIA.length).padStart(2, "0")}</span>
            </div>

            {/* Icon-Only Restrained Navigation */}
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handlePrev}
                aria-label="Previous photograph"
                className="w-8 h-8 rounded-none border border-white/10 hover:border-[#caa35d]/60 bg-white/[0.02] hover:bg-white/[0.06] text-neutral-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#caa35d]"
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <button
                type="button"
                onClick={handleNext}
                aria-label="Next photograph"
                className="w-8 h-8 rounded-none border border-white/10 hover:border-[#caa35d]/60 bg-white/[0.02] hover:bg-white/[0.06] text-neutral-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer focus:outline-none focus:ring-1 focus:ring-[#caa35d]"
              >
                <svg
                  className="w-3.5 h-3.5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Cinematic Horizontal Photographic Rail (Edge-to-Edge Fluid Field) */}
      <div
        {...railProps}
        className="w-full relative focus:outline-none cursor-grab active:cursor-grabbing"
      >
        <div className="max-w-[1520px] mx-auto px-4 sm:px-8 lg:px-12">
          {/* Main Stage: Large Cinematic Photographic Viewport */}
          <div className="relative w-full aspect-[4/3] sm:aspect-[16/10] lg:aspect-[21/10] max-h-[640px] overflow-hidden bg-[#060709] border border-white/10 shadow-2xl rounded-sm">
            {GALLERY_MEDIA.map((item, idx) => {
              const isCurrent = idx === activeIdx;
              const isNeighbor = Math.abs(idx - activeIdx) === 1 || (activeIdx === 0 && idx === GALLERY_MEDIA.length - 1) || (activeIdx === GALLERY_MEDIA.length - 1 && idx === 0);

              return (
                <div
                  key={item.id}
                  className={`absolute inset-0 w-full h-full transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] ${
                    isCurrent
                      ? "opacity-100 scale-100 z-10 pointer-events-auto"
                      : isNeighbor
                      ? "opacity-0 scale-98 z-0 pointer-events-none"
                      : "opacity-0 scale-95 z-0 pointer-events-none"
                  }`}
                >
                  <img
                    src={item.src}
                    alt={item.alt}
                    width={item.width}
                    height={item.height}
                    loading={idx === 0 ? "eager" : "lazy"}
                    decoding="async"
                    className="w-full h-full object-cover object-center grayscale-[10%] hover:grayscale-0 transition-all duration-700"
                  />

                  {/* Atmospheric Subtle Vignette & Natural Category Accent */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20 pointer-events-none" />
                </div>
              );
            })}

            {/* Subtle Minimal Corner Metadata */}
            <div className="absolute bottom-4 left-6 right-6 flex items-center justify-between pointer-events-none z-20">
              <span className="text-[11px] uppercase tracking-[0.2em] text-[#caa35d] font-mono font-semibold">
                {currentItem.category}
              </span>
              <span className="text-[10px] uppercase tracking-widest text-neutral-400 font-mono">
                Midway Studio
              </span>
            </div>
          </div>

          {/* Hairline Continuous Progress Indicator */}
          <div className="mt-6 w-full h-[2px] bg-white/10 relative overflow-hidden">
            <div
              className="absolute top-0 bottom-0 left-0 bg-[#caa35d] transition-all duration-500 ease-out"
              style={{
                width: `${((activeIdx + 1) / GALLERY_MEDIA.length) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
