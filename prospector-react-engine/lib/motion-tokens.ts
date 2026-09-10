export const MOTION_TOKENS = {
  duration: {
    instant: 0.15,
    fast: 0.25,
    normal: 0.45,
    slow: 0.8,
    cinematic: 1.2,
  },
  ease: {
    standard: [0.25, 0.1, 0.25, 1.0],
    outQuart: [0.165, 0.84, 0.44, 1.0],
    inOutCubic: [0.645, 0.045, 0.355, 1.0],
  },
  viewport: {
    once: true,
    amount: 0.2,
    margin: "0px 0px -50px 0px",
  },
} as const;

export const fadeInVariant = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: MOTION_TOKENS.duration.normal,
      ease: MOTION_TOKENS.ease.outQuart,
    },
  },
};
