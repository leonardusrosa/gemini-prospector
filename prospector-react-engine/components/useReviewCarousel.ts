"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseReviewCarouselOptions {
  total: number;
  intervalMs?: number;
  idleResumeMs?: number;
}

export function useReviewCarousel({
  total,
  intervalMs = 7500,
  idleResumeMs = 8500,
}: UseReviewCarouselOptions) {
  const [activeIdx, setActiveIdx] = useState<number>(0);
  const [direction, setDirection] = useState<number>(1);
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const [isFocused, setIsFocused] = useState<boolean>(false);
  const [isManualPaused, setIsManualPaused] = useState<boolean>(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);
  const [isTabHidden, setIsTabHidden] = useState<boolean>(false);

  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check prefers-reduced-motion
  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(mediaQuery.matches);

    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  // Check document visibility
  useEffect(() => {
    if (typeof document === "undefined") return;
    const handleVisibility = () => {
      setIsTabHidden(document.hidden);
    };
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  const triggerManualPause = useCallback(() => {
    setIsManualPaused(true);
    if (idleTimerRef.current) {
      clearTimeout(idleTimerRef.current);
    }
    idleTimerRef.current = setTimeout(() => {
      setIsManualPaused(false);
    }, idleResumeMs);
  }, [idleResumeMs]);

  const handlePrev = useCallback(() => {
    setDirection(-1);
    setActiveIdx((prev) => (prev === 0 ? total - 1 : prev - 1));
    triggerManualPause();
  }, [total, triggerManualPause]);

  const handleNext = useCallback(() => {
    setDirection(1);
    setActiveIdx((prev) => (prev === total - 1 ? 0 : prev + 1));
    triggerManualPause();
  }, [total, triggerManualPause]);

  // Automatic advance
  useEffect(() => {
    if (prefersReducedMotion || isHovered || isFocused || isManualPaused || isTabHidden) {
      return;
    }

    const interval = setInterval(() => {
      setDirection(1);
      setActiveIdx((prev) => (prev === total - 1 ? 0 : prev + 1));
    }, intervalMs);

    return () => clearInterval(interval);
  }, [total, intervalMs, prefersReducedMotion, isHovered, isFocused, isManualPaused, isTabHidden]);

  // Clean up idle timer
  useEffect(() => {
    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        handlePrev();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        handleNext();
      }
    },
    [handlePrev, handleNext]
  );

  return {
    activeIdx,
    direction,
    prefersReducedMotion,
    handlePrev,
    handleNext,
    containerProps: {
      onMouseEnter: () => setIsHovered(true),
      onMouseLeave: () => setIsHovered(false),
      onFocusCapture: () => setIsFocused(true),
      onBlurCapture: () => setIsFocused(false),
      onKeyDown: handleKeyDown,
      tabIndex: 0,
      role: "region",
      "aria-roledescription": "carousel",
      "aria-label": "Selected customer reviews sequence",
    },
  };
}
