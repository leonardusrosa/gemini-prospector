"use client";

import React from "react";
import { LazyMotion, domAnimation, m, AnimatePresence } from "motion/react";
import { PUBLIC_REVIEWS, BUSINESS_INFO } from "@/lib/data";
import { useReviewCarousel } from "./useReviewCarousel";
import { assetPath } from "@/lib/site-paths";

export function Reviews() {
  const {
    activeIdx,
    direction,
    prefersReducedMotion,
    handlePrev,
    handleNext,
    containerProps,
  } = useReviewCarousel({
    total: PUBLIC_REVIEWS.length,
    intervalMs: 7500,
    idleResumeMs: 8500,
  });

  const currentReview = PUBLIC_REVIEWS[activeIdx];

  const slideVariants = {
    enter: (dir: number) => ({
      x: prefersReducedMotion ? 0 : dir > 0 ? 14 : -14,
      opacity: 0,
    }),
    center: {
      x: 0,
      opacity: 1,
      transition: {
        duration: prefersReducedMotion ? 0.05 : 0.5,
        ease: [0.16, 1, 0.3, 1] as const,
      },
    },
    exit: (dir: number) => ({
      x: prefersReducedMotion ? 0 : dir > 0 ? -14 : 14,
      opacity: 0,
      transition: {
        duration: prefersReducedMotion ? 0.05 : 0.4,
        ease: [0.16, 1, 0.3, 1] as const,
      },
    }),
  };

  return (
    <section
      id="reviews"
      data-role="reviews"
      data-motion="reveal"
      className="w-full py-24 md:py-32 bg-[#14171f] text-white border-t border-white/[0.06] overflow-hidden"
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-10 lg:px-16">
        {/* Header & Aggregate Provenance */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16 md:mb-20">
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-3 text-xs uppercase tracking-[0.25em] font-semibold text-[#caa35d] mb-4">
              <span>[ 03 — REVIEWS ]</span>
              <div className="h-[1px] w-6 bg-[#caa35d]/40" />
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold font-display uppercase tracking-tight leading-tight">
              COMMUNITY FEEDBACK
            </h2>
          </div>

          <div className="flex items-baseline gap-4 font-display">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl sm:text-5xl font-extrabold text-white">
                {BUSINESS_INFO.rating}
              </span>
              <span className="text-lg text-neutral-400 font-light">/ 5</span>
            </div>
            <div className="text-xs uppercase tracking-widest text-neutral-400 font-mono pl-4 border-l border-white/15">
              <span>{BUSINESS_INFO.reviewCount} Reviews</span>
            </div>
          </div>
        </div>

        {/* Main Review Stage: Dominant Spotlight with Controlled Editorial Controls */}
        <div
          {...containerProps}
          data-role="reviews-carousel"
          data-review-curated-subset="true"
          data-review-total-items={PUBLIC_REVIEWS.length}
          data-review-curated-ids={PUBLIC_REVIEWS.map((review) => review.id).join(",")}
          data-review-curated-native-ids={PUBLIC_REVIEWS.map((review) => review.nativeReviewId).join(",")}
          className="relative bg-[#0d1016] border border-white/10 p-6 sm:p-10 lg:p-12 rounded-sm shadow-2xl focus:outline-none focus:border-[#caa35d]/40 transition-colors"
        >
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">
            {/* Dominant Spotlight Stage */}
            <div className="lg:col-span-8 flex flex-col justify-center min-h-[300px] sm:min-h-[280px]">
              {/* Top Row: Quotation Mark + Position Indicator + Icon Controls */}
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/[0.06]">
                <span className="text-4xl sm:text-5xl font-display text-[#caa35d]/30 select-none leading-none">
                  “
                </span>

                {/* Subtle Position Indicator + Restrained Icon Controls */}
                <div className="flex items-center gap-4 sm:gap-5">
                  <div className="font-mono text-xs text-neutral-400 tracking-wider">
                    <span className="text-[#caa35d] font-semibold">
                      {String(activeIdx + 1).padStart(2, "0")}
                    </span>
                    <span className="text-neutral-600">{" / "}</span>
                    <span>{String(PUBLIC_REVIEWS.length).padStart(2, "0")}</span>
                  </div>

                  {/* Icon Only Navigation */}
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={handlePrev}
                      aria-label="Previous review"
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
                      aria-label="Next review"
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

              {/* Animated Editorial Quote & Attribution */}
              <div className="relative overflow-hidden min-h-[160px] sm:min-h-[140px] flex flex-col justify-between">
                <LazyMotion features={domAnimation}>
                  <AnimatePresence initial={false} mode="wait" custom={direction}>
                    <m.div
                      key={currentReview.id}
                      data-role="review-carousel-item"
                      data-review-evidence-id={currentReview.id}
                      data-review-native-id={currentReview.nativeReviewId}
                      data-review-entry-fingerprint={currentReview.fingerprint}
                      data-review-rating={currentReview.rating}
                      data-review-translation-state={currentReview.translationState}
                      data-review-source-locale={currentReview.sourceLocale}
                      custom={direction}
                      variants={slideVariants}
                      initial="enter"
                      animate="center"
                      exit="exit"
                      className="flex flex-col justify-between h-full"
                    >
                      <blockquote className="text-lg sm:text-xl lg:text-2xl font-light font-display text-neutral-100 leading-snug tracking-tight">
                        {currentReview.quote}
                      </blockquote>

                      <div className="mt-8 flex flex-wrap items-center gap-3 sm:gap-5 text-sm pt-6 border-t border-white/10">
                        <span className="font-semibold text-white tracking-wider uppercase font-display text-xs">
                          {currentReview.author}
                        </span>
                        <span className="text-neutral-600">•</span>
                        <span className="text-[11px] uppercase tracking-widest text-[#caa35d] font-semibold font-mono">
                          {currentReview.serviceFocus}
                        </span>
                        <span className="text-neutral-600">•</span>
                        <span className="text-[11px] uppercase tracking-widest text-neutral-400 font-mono">
                          {currentReview.tag}
                        </span>
                      </div>
                    </m.div>
                  </AnimatePresence>
                </LazyMotion>
              </div>
            </div>

            {/* Contextual Visual: Optical Surface Reflection Detail */}
            <div className="lg:col-span-4 relative aspect-[4/5] overflow-hidden bg-[#080a0d] shadow-xl border border-white/10 rounded-sm">
              <img
                src={assetPath("reviews-reflection-detail.webp")}
                alt="Black vehicle body surface under reflected overhead lighting"
                loading="eager"
                decoding="async"
                className="w-full h-full object-cover object-center grayscale-[15%] hover:grayscale-0 transition-all duration-700 hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0d1016] via-transparent to-transparent pointer-events-none" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
