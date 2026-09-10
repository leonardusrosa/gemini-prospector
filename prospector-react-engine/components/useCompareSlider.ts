import { useState, useRef, useEffect, useCallback } from "react";

export function useCompareSlider(initialPos: number = 50) {
  const [sliderPos, setSliderPos] = useState<number>(initialPos);
  const [isInteracting, setIsInteracting] = useState<boolean>(false);
  const animFrameRef = useRef<number | null>(null);
  const dirRef = useRef<number>(1);
  const containerRef = useRef<HTMLDivElement>(null);

  const updatePositionFromClientX = useCallback((clientX: number) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    setSliderPos(percentage);
  }, []);

  // Smooth auto-slide demonstration when idle (disabled under reduced motion)
  const runAutoSlide = useCallback(() => {
    if (isInteracting) return;
    setSliderPos((prev) => {
      let next = prev + dirRef.current * 0.2;
      if (next >= 95) {
        dirRef.current = -1;
        next = 95;
      } else if (next <= 5) {
        dirRef.current = 1;
        next = 5;
      }
      return next;
    });
    animFrameRef.current = requestAnimationFrame(runAutoSlide);
  }, [isInteracting]);

  useEffect(() => {
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!isInteracting && !prefersReducedMotion) {
      animFrameRef.current = requestAnimationFrame(runAutoSlide);
    }
    return () => {
      if (animFrameRef.current !== null) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isInteracting, runAutoSlide]);

  const handlePointerDown = (e: React.PointerEvent) => {
    setIsInteracting(true);
    if (animFrameRef.current !== null) {
      cancelAnimationFrame(animFrameRef.current);
    }
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    updatePositionFromClientX(e.clientX);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isInteracting) return;
    updatePositionFromClientX(e.clientX);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    setIsInteracting(false);
    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      // Pointer capture lost
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft") {
      setIsInteracting(true);
      setSliderPos((prev) => Math.max(0, prev - 5));
    } else if (e.key === "ArrowRight") {
      setIsInteracting(true);
      setSliderPos((prev) => Math.min(100, prev + 5));
    }
  };

  return {
    sliderPos,
    isInteracting,
    containerRef,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handleKeyDown,
  };
}
