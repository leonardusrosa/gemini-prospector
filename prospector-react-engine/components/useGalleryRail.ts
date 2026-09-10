"use client";

import { useState, useEffect, useRef, useCallback } from "react";

interface UseGalleryRailOptions {
  total: number;
  intervalMs?: number;
  idleResumeMs?: number;
}

export function useGalleryRail({
  total,
  intervalMs = 6500,
  idleResumeMs = 8000,
}: UseGalleryRailOptions) {
  const [activeIdx, setActiveIdx] = useState<number>(0);
  const [isHovered, setIsHovered] = useState<boolean>(false);
  const [isFocused, setIsFocused] = useState<boolean>(false);
  const [isManualPaused, setIsManualPaused] = useState<boolean>(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(false);
  const [isTabHidden, setIsTabHidden] = useState<boolean>(false);

  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);
  const touchStartX = useRef<number | null>(null);

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
    setActiveIdx((prev) => (prev === 0 ? total - 1 : prev - 1));
    triggerManualPause();
  }, [total, triggerManualPause]);

  const handleNext = useCallback(() => {
    setActiveIdx((prev) => (prev === total - 1 ? 0 : prev + 1));
    triggerManualPause();
  }, [total, triggerManualPause]);

  const goTo = useCallback(
    (index: number) => {
      setActiveIdx(Math.max(0, Math.min(index, total - 1)));
      triggerManualPause();
    },
    [total, triggerManualPause]
  );

  // Auto-advance
  useEffect(() => {
    if (prefersReducedMotion || isHovered || isFocused || isManualPaused || isTabHidden) {
      return;
    }

    const interval = setInterval(() => {
      setActiveIdx((prev) => (prev === total - 1 ? 0 : prev + 1));
    }, intervalMs);

    return () => clearInterval(interval);
  }, [total, intervalMs, prefersReducedMotion, isHovered, isFocused, isManualPaused, isTabHidden]);

  // Clean up timer
  useEffect(() => {
    return () => {
      if (idleTimerRef.current) {
        clearTimeout(idleTimerRef.current);
      }
    };
  }, []);

  // Touch Swipe Handlers
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const touchEndX = e.changedTouches[0].clientX;
    const diffX = touchStartX.current - touchEndX;
    if (Math.abs(diffX) > 40) {
      if (diffX > 0) {
        handleNext();
      } else {
        handlePrev();
      }
    }
    touchStartX.current = null;
  };

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      handlePrev();
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      handleNext();
    }
  };

  return {
    activeIdx,
    prefersReducedMotion,
    handlePrev,
    handleNext,
    goTo,
    railProps: {
      onMouseEnter: () => setIsHovered(true),
      onMouseLeave: () => setIsHovered(false),
      onFocusCapture: () => setIsFocused(true),
      onBlurCapture: () => setIsFocused(false),
      onTouchStart: handleTouchStart,
      onTouchEnd: handleTouchEnd,
      onKeyDown: handleKeyDown,
      tabIndex: 0,
      role: "region",
      "aria-roledescription": "carousel",
      "aria-label": "Dallas Detailing studio photography gallery",
    },
  };
}
