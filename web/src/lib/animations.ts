import { Variants } from "framer-motion";

// ============================================================================
// FADE ANIMATIONS
// ============================================================================

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3 } },
};

export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

export const fadeInDown: Variants = {
  hidden: { opacity: 0, y: -20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

// ============================================================================
// SCALE ANIMATIONS
// ============================================================================

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: "easeOut" } },
};

export const scaleInBounce: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: "spring", stiffness: 300, damping: 20 },
  },
};

// ============================================================================
// SLIDE ANIMATIONS
// ============================================================================

export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -30 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 30 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: "easeOut" } },
};

// ============================================================================
// STAGGER CONTAINER ANIMATIONS
// ============================================================================

export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

export const staggerContainerFast: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.05,
    },
  },
};

// ============================================================================
// STAGGER ITEM ANIMATIONS
// ============================================================================

export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" } },
};

export const staggerItemScale: Variants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.3, ease: "easeOut" } },
};

// ============================================================================
// PAGE TRANSITION ANIMATIONS
// ============================================================================

export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { 
    opacity: 1, 
    y: 0, 
    transition: { duration: 0.3, ease: "easeOut" } 
  },
  exit: { 
    opacity: 0, 
    y: -10, 
    transition: { duration: 0.2, ease: "easeIn" } 
  },
};

// ============================================================================
// CARD HOVER ANIMATIONS
// ============================================================================

export const cardHover = {
  scale: 1.02,
  y: -4,
  transition: { type: "spring" as const, stiffness: 300, damping: 20 },
};

export const cardTap = {
  scale: 0.98,
  transition: { type: "spring" as const, stiffness: 300, damping: 20 },
};

// ============================================================================
// BUTTON ANIMATIONS
// ============================================================================

export const buttonHover = {
  scale: 1.02,
  transition: { type: "spring" as const, stiffness: 400, damping: 20 },
};

export const buttonTap = {
  scale: 0.98,
  transition: { type: "spring" as const, stiffness: 400, damping: 20 },
};

// ============================================================================
// SKELETON PULSE ANIMATION (CSS alternative for framer-motion)
// ============================================================================

export const pulse: Variants = {
  visible: {
    opacity: [0.5, 1, 0.5],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};

// ============================================================================
// TOOLTIP / POPOVER ANIMATIONS
// ============================================================================

export const tooltipVariants: Variants = {
  hidden: { opacity: 0, scale: 0.96, y: -4 },
  visible: { 
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: { duration: 0.15, ease: "easeOut" },
  },
  exit: { 
    opacity: 0, 
    scale: 0.96, 
    y: -4,
    transition: { duration: 0.1, ease: "easeIn" },
  },
};

// ============================================================================
// MODAL / DIALOG ANIMATIONS
// ============================================================================

export const overlayVariants: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.2 } },
  exit: { opacity: 0, transition: { duration: 0.15 } },
};

export const modalVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95, y: 20 },
  visible: { 
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: { type: "spring", stiffness: 300, damping: 25 },
  },
  exit: { 
    opacity: 0, 
    scale: 0.95, 
    y: 20,
    transition: { duration: 0.15, ease: "easeIn" },
  },
};

// ============================================================================
// LIST ITEM ANIMATIONS (for drag-and-drop or reordering)
// ============================================================================

export const listItemVariants: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: 20, transition: { duration: 0.2 } },
};

// ============================================================================
// NOTIFICATION / TOAST ANIMATIONS
// ============================================================================

export const notificationVariants: Variants = {
  hidden: { opacity: 0, y: -20, scale: 0.95 },
  visible: { 
    opacity: 1, 
    y: 0, 
    scale: 1,
    transition: { type: "spring", stiffness: 400, damping: 25 },
  },
  exit: { 
    opacity: 0, 
    y: -20, 
    scale: 0.95,
    transition: { duration: 0.2, ease: "easeIn" },
  },
};

// ============================================================================
// ACCORDION / COLLAPSE ANIMATIONS
// ============================================================================

export const accordionVariants: Variants = {
  hidden: { height: 0, opacity: 0 },
  visible: { 
    height: "auto", 
    opacity: 1,
    transition: { duration: 0.3, ease: "easeOut" },
  },
  exit: { 
    height: 0, 
    opacity: 0,
    transition: { duration: 0.2, ease: "easeIn" },
  },
};

// ============================================================================
// SPRING CONFIGURATIONS
// ============================================================================

export const springConfig = {
  gentle: { type: "spring" as const, stiffness: 120, damping: 14 },
  snappy: { type: "spring" as const, stiffness: 300, damping: 20 },
  bouncy: { type: "spring" as const, stiffness: 400, damping: 15 },
  stiff: { type: "spring" as const, stiffness: 500, damping: 30 },
};
