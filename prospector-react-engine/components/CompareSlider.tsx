"use client";

import React from "react";
import { useCompareSlider } from "./useCompareSlider";
import { assetPath } from "@/lib/site-paths";

export function CompareSlider() {
  const {
    sliderPos,
    isInteracting,
    containerRef,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handleKeyDown,
  } = useCompareSlider(50);

  // Dynamic badge opacity based on handle distance to prevent visual overlap
  const beforeOpacity = Math.max(0.2, Math.min(1, sliderPos / 25));
  const afterOpacity = Math.max(0.2, Math.min(1, (100 - sliderPos) / 25));

  return (
    <section
      id="comparison"
      data-role="signature-section"
      className="w-full py-24 md:py-32 bg-[#08090b] text-white border-t border-white/[0.06] overflow-hidden"
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16">
        {/* Concise Section Header */}
        <div className="max-w-2xl mb-12 sm:mb-16">
          <div className="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[#caa35d] mb-3">
            <span>[ 02 — COMPARISON ]</span>
            <div className="h-[1px] w-6 bg-[#caa35d]/40" />
          </div>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-display uppercase tracking-tight leading-tight">
            INTERIOR IMAGE COMPARISON
          </h2>
          <p className="text-xs text-neutral-400">
            Drag or tap the divider to inspect the reference images.
          </p>
        </div>

        {/* Cinematic Visual Stage (Full 3:4 Aspect Display — Zero Cropping) */}
        <div className="w-full bg-[#050608] border border-white/10 rounded-sm p-4 sm:p-8 lg:p-12 flex items-center justify-center shadow-2xl">
          <div
            ref={containerRef}
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onKeyDown={handleKeyDown}
            tabIndex={0}
            role="slider"
            aria-label="Reference interior comparison slider"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(sliderPos)}
            className="relative w-full max-w-[640px] aspect-[3/4] overflow-hidden cursor-ew-resize select-none touch-none focus:outline-none focus:ring-1 focus:ring-[#caa35d] shadow-2xl border border-white/10 bg-[#040406]"
          >
            {/* Base Layer: After (Full image visible, object-contain, aspect preserved) */}
            <img
              src={assetPath("compare-after.webp")}
              alt="Automotive interior comparison image"
              loading="lazy"
              decoding="async"
              className="absolute inset-0 w-full h-full object-contain object-center pointer-events-none"
            />

            {/* Clipped Top Layer: Before (Full image visible, object-contain, aspect preserved) */}
            <div
              className="absolute inset-0 w-full h-full pointer-events-none overflow-hidden will-change-[clip-path]"
              style={{
                clipPath: `inset(0 calc(100% - ${sliderPos}%) 0 0)`,
              }}
            >
              <img
                src={assetPath("compare-before.webp")}
                alt="Automotive interior reference image"
                loading="lazy"
                decoding="async"
                className="absolute inset-0 w-full h-full object-contain object-center"
              />
            </div>

            {/* Divider Line & Damped Handle */}
            <div
              className="absolute top-0 bottom-0 w-[1.5px] bg-white pointer-events-none shadow-[0_0_12px_rgba(255,255,255,0.9)] will-change-[left]"
              style={{ left: `${sliderPos}%` }}
            >
              <div
                className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-none bg-[#08090b] border border-[#caa35d] flex items-center justify-center cursor-ew-resize transition-all duration-150"
                style={{
                  transform: `translate(-50%, -50%) scale(${isInteracting ? 1.08 : 1.0})`,
                  boxShadow: isInteracting
                    ? "0 0 20px rgba(202,163,93,0.6)"
                    : "0 4px 12px rgba(0,0,0,0.8)",
                }}
              >
                <span className="text-[#caa35d] text-[10px] font-mono font-bold tracking-tighter">
                  ↔
                </span>
              </div>
            </div>

            {/* High-Contrast Directional Badges */}
            <div
              className="absolute top-4 sm:top-6 left-4 sm:left-6 pointer-events-none transition-opacity duration-300"
              style={{ opacity: beforeOpacity }}
            >
              <span className="px-3 py-1 text-[11px] font-mono font-bold tracking-widest uppercase bg-black/85 text-neutral-300 border border-white/20">
                REFERENCE
              </span>
            </div>
            <div
              className="absolute top-4 sm:top-6 right-4 sm:right-6 pointer-events-none transition-opacity duration-300"
              style={{ opacity: afterOpacity }}
            >
              <span className="px-3 py-1 text-[11px] font-mono font-bold tracking-widest uppercase bg-[#caa35d] text-black font-bold border border-[#caa35d]">
                COMPARISON
              </span>
            </div>

            {/* Telemetry Coordinate Indicator */}
            <div className="absolute bottom-4 sm:bottom-6 left-4 sm:left-6 pointer-events-none">
              <span className="text-[10px] uppercase font-mono tracking-widest text-neutral-400 bg-black/75 px-2.5 py-1 border border-white/10">
                AXIS: {Math.round(sliderPos)}% {isInteracting ? "[ENGAGED]" : "[AUTONOMOUS]"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
