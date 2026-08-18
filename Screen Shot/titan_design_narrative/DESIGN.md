---
name: Titan Design Narrative
colors:
  surface: '#fcf9f1'
  surface-dim: '#dcdad2'
  surface-bright: '#fcf9f1'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3eb'
  surface-container: '#f1eee6'
  surface-container-high: '#ebe8e0'
  surface-container-highest: '#e5e2da'
  on-surface: '#1c1c17'
  on-surface-variant: '#424654'
  inverse-surface: '#31312b'
  inverse-on-surface: '#f3f1e9'
  outline: '#737786'
  outline-variant: '#c2c6d7'
  surface-tint: '#0056d0'
  primary: '#0054cb'
  on-primary: '#ffffff'
  primary-container: '#2c6dec'
  on-primary-container: '#fefcff'
  inverse-primary: '#b1c5ff'
  secondary: '#575d78'
  on-secondary: '#ffffff'
  secondary-container: '#d8defe'
  on-secondary-container: '#5b617d'
  tertiary: '#735c00'
  on-tertiary: '#ffffff'
  tertiary-container: '#cba72f'
  on-tertiary-container: '#4e3d00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b1c5ff'
  on-primary-fixed: '#001847'
  on-primary-fixed-variant: '#0040a0'
  secondary-fixed: '#dce1ff'
  secondary-fixed-dim: '#bfc5e4'
  on-secondary-fixed: '#141a32'
  on-secondary-fixed-variant: '#3f465f'
  tertiary-fixed: '#ffe088'
  tertiary-fixed-dim: '#e9c349'
  on-tertiary-fixed: '#241a00'
  on-tertiary-fixed-variant: '#574500'
  background: '#fcf9f1'
  on-background: '#1c1c17'
  surface-variant: '#e5e2da'
typography:
  display-lg:
    fontFamily: Montserrat
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-lg:
    fontFamily: Montserrat
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Montserrat
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Montserrat
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
  label-sm:
    fontFamily: Inter
    fontSize: 10px
    fontWeight: '500'
    lineHeight: '1'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 64px
  container-max: 1280px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The brand persona is an authoritative yet high-energy mentor—someone who is established in their field but remains at the cutting edge of technology. The design system targets professional learners and enterprise teams who require a high-performance environment that feels premium and reliable.

The aesthetic follows a **Modern Corporate** style with **Glassmorphic** accents. It balances the stability of deep navy with the vitality of electric blue and gold. The interface relies on spacious layouts, high-quality typography, and subtle tactile depth to create an atmosphere of focused ambition and academic excellence in a digital-first era.

## Colors

The palette is built on a foundation of high-contrast depth. 
- **Deep Navy (#0A1128)** serves as the anchor, used for headers, dark mode backgrounds, and primary text to establish trust.
- **Electric Blue (#3E7BFA)** is the energetic driver, reserved for primary actions, progress indicators, and active states.
- **Warm Gold (#D4AF37)** and **Glow Gold (#F4CD7C)** are used strictly for moments of "Reward" and "Attention"—achievements, badges, and high-priority CTAs.
- **Off-white/Cream (#F5F2EA)** replaces pure white for light-mode backgrounds to reduce eye strain during long learning sessions and to provide a sophisticated, editorial feel.

Gradients should transition from Deep Navy to Electric Blue for a "tech-forward" depth, or utilize a soft Glow Gold radial highlight for achievement states.

## Typography

This design system uses a dual-font strategy to balance impact with readability.
- **Montserrat** provides geometric strength for display and headlines. Its bold weights communicate the "Titan" personality—strong, modern, and unmistakable.
- **Inter** is used for all functional text. Its high x-height and systematic clarity ensure that dense learning materials remain legible across all devices.

Maintain a strict hierarchy where Montserrat is reserved for titles and major section headers, while Inter handles all instructional, body, and UI-specific labeling.

## Layout & Spacing

The layout utilizes a **12-column fluid grid** for desktop, transitioning to a **4-column grid** for mobile. 

A strict 8px spatial system governs all margins and padding. Content should be housed within "Modern Cards" that use a 24px inner padding (lg) to ensure elements have room to breathe. 

**Reflow Rules:**
- **Desktop:** 12 columns, 24px gutters, max-width of 1280px.
- **Tablet:** 8 columns, 16px gutters, full width with 24px side margins.
- **Mobile:** 4 columns, 16px gutters, full width with 16px side margins. Horizontal scrolling sections are preferred over long vertical lists for course catalogs on mobile.

## Elevation & Depth

This design system employs a **Tonal Layering** approach combined with **Glassmorphism** for navigation elements.

1.  **Level 0 (Surface):** The Off-white/Cream base layer (#F5F2EA).
2.  **Level 1 (Cards):** White surfaces with a very soft, diffused shadow (0px 4px 20px rgba(10, 17, 40, 0.05)).
3.  **Level 2 (Interaction):** On hover, cards lift slightly with a more pronounced shadow and a 1px stroke of Electric Blue at 10% opacity.
4.  **Glassmorphism:** Navigation bars and sticky headers use a backdrop-filter (blur: 12px) with a semi-transparent Deep Navy (alpha 0.8) or White (alpha 0.7) depending on the underlying theme. This creates a tech-forward "HUD" feel.

## Shapes

The shape language is defined by a "Rounded Modern" ethos. 
- **Small components (Inputs, Buttons):** Use a 0.5rem (8px) radius.
- **Main Containers (Cards, Modals):** Use the `rounded-lg` token at 1rem (16px) to create a friendly but structured appearance.
- **Avatars & Progress Rings:** Always circular (full pill) to contrast against the rectangular grid.

Corners should never be sharp, as the roundedness conveys the "approachable/modern" aspect of the brand's personality.

## Components

### Buttons & Inputs
- **Primary Button:** Electric Blue fill, White text, 0.5rem radius. Hover state adds a subtle Glow Gold outer shadow.
- **Secondary Button:** Deep Navy outline (1px), Deep Navy text.
- **Input Fields:** Soft Cream background (slightly darker than page surface), 1px border (#D1D5DB). On focus, the border transitions to Electric Blue with a 2px outer glow.

### Cards & Chips
- **Course Cards:** 1rem radius, Level 1 shadow, Montserrat Semibold for titles. Includes a bottom-aligned progress bar in Electric Blue.
- **Achievement Chips:** Gold background (#D4AF37) with high-contrast Navy text, used to signify course completion.

### Specialized LMS Components
- **Progress Bars:** Thin 4px height, using a Deep Navy track and Electric Blue fill. For "Completed" states, the fill transitions to Glow Gold.
- **Navigation:** Top-fixed with glassmorphic blur. Active links use a 3px bottom-border highlight in Electric Blue.
- **Lesson Sidebar:** Clean, minimal list with Inter 14px text. Active lesson is highlighted with a soft Electric Blue background tint (10% opacity) and a bold left-edge accent.