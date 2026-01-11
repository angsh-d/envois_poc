# Apple-Inspired Minimalist Design System

## Design Philosophy

> **Build applications that look and feel like Apple products.**
> 
> This design system captures the essence of Apple's design language: obsessive attention to detail, 
> premium materials and controls, generous whitespace, refined typography, and subtle interactions 
> that delight users. Every element should feel intentional, polished, and effortlessly elegant.

---

## Core Design Principles

### 1. Premium Look & Feel
- **Use premium UI controls** - shadcn/ui, Radix UI, or equivalent high-quality component libraries
- **No cheap-looking elements** - Avoid default browser styles, basic HTML controls, or unpolished components
- **Attention to micro-interactions** - Smooth transitions, subtle hover states, refined animations
- **High-quality assets** - Crisp icons (Lucide), professional typography, optimized images

### 2. Apple Design DNA
- **Clarity** - Text is legible at every size, icons are precise, adornments are subtle
- **Deference** - Content is primary, chrome is minimal, UI enhances but never competes
- **Depth** - Visual layers and realistic motion convey hierarchy and facilitate understanding

### 3. Minimalism as a Feature
- **Subtract, don't add** - Remove every element that doesn't serve a purpose
- **Whitespace is content** - Generous padding creates breathing room and focus
- **Monochromatic confidence** - Black, white, and grays with purpose

---

## Color Palette

### Primary Colors (Grayscale)
```css
:root {
  /* Core */
  --white: #ffffff;
  --black: #000000;
  
  /* Gray Scale - Apple-inspired */
  --gray-50: #f9fafb;
  --gray-100: #f3f4f6;
  --gray-200: #e5e7eb;
  --gray-300: #d1d5db;
  --gray-400: #9ca3af;
  --gray-500: #6b7280;
  --gray-600: #4b5563;
  --gray-700: #374151;
  --gray-800: #1f2937;
  --gray-900: #111827;
  
  /* Semantic */
  --background: #ffffff;
  --foreground: #000000;
  --border: #e5e7eb;
  --muted: #6b7280;
  --muted-light: #9ca3af;
}
```

### Color Usage Guidelines
| Element | Color | Notes |
|---------|-------|-------|
| Backgrounds | White (`#ffffff`) | Pure, clean canvas |
| Primary Text | Black (`#000000`) | Maximum contrast |
| Secondary Text | Gray-600 (`#4b5563`) | Subtle hierarchy |
| Muted Text | Gray-500 (`#6b7280`) | Tertiary info |
| Borders | Gray-200 (`#e5e7eb`) | Thin, subtle |
| Dividers | Gray-300 (`#d1d5db`) | Visual separation |
| Hover States | Gray-100 (`#f3f4f6`) | Subtle feedback |

---

## Typography

### Font Stack (System Native)
```css
font-family: "Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

### Font Rendering
```css
body {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-feature-settings: "rlig" 1, "calt" 1;
}
```

### Type Scale

| Element | Size (Mobile) | Size (Desktop) | Weight | Tracking | Line Height |
|---------|---------------|----------------|--------|----------|-------------|
| **Hero H1** | 60px (`text-6xl`) | 72px (`text-7xl`) | 600 (`font-semibold`) | tight | tight |
| **Section H2** | 36px (`text-4xl`) | 48px (`text-5xl`) | 600 (`font-semibold`) | tight | tight |
| **Card Title** | 20px (`text-xl`) | 24px (`text-2xl`) | 600 (`font-semibold`) | normal | normal |
| **Subtitle** | 20px (`text-xl`) | 24px (`text-2xl`) | 300 (`font-light`) | normal | relaxed |
| **Body Large** | 18px (`text-lg`) | 18px (`text-lg`) | 400 (`font-normal`) | normal | relaxed |
| **Body** | 16px (`text-base`) | 16px (`text-base`) | 400 (`font-normal`) | normal | normal |
| **Small** | 14px (`text-sm`) | 14px (`text-sm`) | 400 (`font-normal`) | normal | normal |
| **Caption** | 12px (`text-xs`) | 12px (`text-xs`) | 500 (`font-medium`) | normal | normal |

### Tailwind Typography Classes
```jsx
// Hero Headline
<h1 className="text-6xl md:text-7xl font-semibold leading-tight tracking-tight text-black">

// Section Headline  
<h2 className="text-4xl md:text-5xl font-semibold tracking-tight text-black">

// Subtitle (Light)
<p className="text-xl md:text-2xl font-light text-gray-600 leading-relaxed">

// Body Text
<p className="text-lg text-gray-500 leading-relaxed">
```

---

## Top Navbar Specification

### Design Requirements
- Height: **52px** (fixed)
- Position: **Sticky** at top
- Background: **Pure white** with subtle shadow
- Border: **1px bottom** in gray-200

### Complete Implementation
```jsx
<nav className="bg-white px-6 py-3 sticky top-0 z-50 shadow-sm border-b border-gray-200">
  <div className="max-w-full mx-auto flex items-center justify-between gap-8">
    
    {/* LEFT: Logo & Brand */}
    <div className="flex items-center gap-3 flex-shrink-0">
      <img src="/logo.png" alt="Logo" className="h-10 flex-shrink-0" />
      <div className="w-px h-8 bg-gray-300 flex-shrink-0"></div>
      <span className="text-gray-600 font-light text-xl leading-none">
        Platform Name
      </span>
    </div>

    {/* CENTER: Search Bar (Premium Pill Style) */}
    <div className="hidden lg:flex flex-1 max-w-2xl mx-8">
      <div className="relative w-full">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <SearchIcon className="w-5 h-5 text-gray-400" />
        </div>
        <input
          type="text"
          className="block w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-full bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:border-transparent text-sm"
          placeholder="Search..."
        />
      </div>
    </div>

    {/* RIGHT: User Avatar */}
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center">
        <span className="text-white font-semibold text-xs">JD</span>
      </div>
    </div>

  </div>
</nav>
```

### Navbar Component Specs
| Element | Specification |
|---------|--------------|
| Logo | Height: 40px (`h-10`), no shrink |
| Divider | Width: 1px, Height: 32px, Color: gray-300 |
| Brand Text | Size: 20px, Weight: light, Color: gray-600 |
| Search Input | Max-width: 672px, Pill-shaped (`rounded-full`) |
| Avatar | Size: 32×32px, Black background, White text |

---

## Hero Section Specification

### Design Requirements
- Padding: **192px vertical** (generous whitespace)
- Alignment: **Center**
- Max-width: **896px** for text content

### Complete Implementation
```jsx
<section className="py-48 px-6 bg-white">
  <div className="max-w-4xl mx-auto text-center">
    
    {/* Main Headline */}
    <h1 className="text-6xl md:text-7xl font-semibold mb-8 leading-tight tracking-tight text-black">
      Intelligent AI Agents
    </h1>
    
    {/* Subtitle */}
    <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-12 leading-relaxed font-light">
      Across the Clinical Trial Lifecycle
    </p>
    
    {/* Description */}
    <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-16 leading-relaxed">
      Agentic AI that reasons, plans, acts autonomously, and adapts to optimize 
      clinical research from protocol design through regulatory submission.
    </p>

    {/* Premium Button Group */}
    <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
      
      {/* Primary Button */}
      <button className="bg-black text-white hover:bg-gray-900 font-semibold px-12 py-4 text-base rounded-full shadow-none transition-all duration-300">
        Explore Agents
      </button>
      
      {/* Secondary Button */}
      <button className="bg-white border-2 border-black text-black hover:bg-black hover:text-white font-semibold px-12 py-4 text-base rounded-full transition-all duration-300">
        Launch Demo
      </button>

    </div>
  </div>
</section>
```

---

## Premium UI Controls

### Buttons (Apple-Style)

#### Primary Button
```jsx
<button className="bg-black text-white hover:bg-gray-900 font-semibold px-12 py-4 text-base rounded-full shadow-none transition-all duration-300">
  Primary Action
</button>
```

#### Secondary Button (Outline)
```jsx
<button className="bg-white border-2 border-black text-black hover:bg-black hover:text-white font-semibold px-12 py-4 text-base rounded-full transition-all duration-300">
  Secondary Action
</button>
```

#### Ghost Button
```jsx
<button className="bg-transparent text-gray-600 hover:text-black hover:bg-gray-100 font-medium px-6 py-2 rounded-full transition-colors duration-200">
  Ghost Action
</button>
```

#### Small Button
```jsx
<button className="bg-black text-white hover:bg-gray-900 font-medium px-6 py-2 text-sm rounded-full transition-all duration-200">
  Small Action
</button>
```

### Input Fields (Premium Style)

#### Standard Input
```jsx
<input
  type="text"
  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-gray-400 focus:border-transparent bg-white text-gray-900 placeholder-gray-500 transition-all duration-200"
  placeholder="Enter text..."
/>
```

#### Pill Input (Search)
```jsx
<input
  type="text"
  className="w-full px-4 py-2.5 border border-gray-300 rounded-full focus:ring-2 focus:ring-gray-400 focus:border-transparent bg-white text-sm placeholder-gray-500"
  placeholder="Search..."
/>
```

### Cards (Premium Style)

#### Standard Card
```jsx
<div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm hover:shadow-md transition-all duration-300">
  <h3 className="text-xl font-semibold text-black mb-3">Card Title</h3>
  <p className="text-gray-600">Card content goes here.</p>
</div>
```

#### Interactive Card
```jsx
<div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer">
  <h3 className="text-xl font-semibold text-black mb-3">Interactive Card</h3>
  <p className="text-gray-600">Click to interact.</p>
</div>
```

---

## Spacing System

### Section Padding
| Section Type | Vertical | Horizontal | Tailwind |
|--------------|----------|------------|----------|
| Hero | 192px | 24px | `py-48 px-6` |
| Major Section | 128px | 24px | `py-32 px-6` |
| Standard Section | 96px | 24px | `py-24 px-6` |
| Compact Section | 64px | 24px | `py-16 px-6` |

### Content Max Widths
| Content Type | Width | Tailwind |
|--------------|-------|----------|
| Full Page | 1280px | `max-w-7xl` |
| Hero Text | 896px | `max-w-4xl` |
| Subtitle | 768px | `max-w-3xl` |
| Description | 672px | `max-w-2xl` |
| Search Bar | 672px | `max-w-2xl` |

### Gaps
| Use Case | Size | Tailwind |
|----------|------|----------|
| Button groups | 24px | `gap-6` |
| Card grids | 24px | `gap-6` |
| Nav sections | 32px | `gap-8` |
| Logo elements | 12px | `gap-3` |
| Inline items | 8px | `gap-2` |

---

## Shadows

### Shadow Scale
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
```

### Usage
| State | Shadow | Tailwind |
|-------|--------|----------|
| Default Card | sm | `shadow-sm` |
| Hover Card | md or lg | `hover:shadow-md` |
| Navbar | sm | `shadow-sm` |
| Modal/Dropdown | xl | `shadow-xl` |

---

## Animations & Transitions

### Standard Transitions
```jsx
// All properties (standard)
className="transition-all duration-300"

// Color only (fast)
className="transition-colors duration-200"

// Transform only
className="transition-transform duration-300"
```

### Hover Effects
```jsx
// Lift on hover
className="hover:-translate-y-1 transition-transform duration-300"

// Shadow on hover
className="hover:shadow-lg transition-shadow duration-300"

// Color invert (buttons)
className="hover:bg-black hover:text-white transition-all duration-300"
```

### Fade In Animation
```css
@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
```

---

## Custom Scrollbars

```css
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
```

---

## Required Dependencies

### Package.json
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "tailwindcss": "^3.4.0",
    "tailwindcss-animate": "^1.0.7",
    "@tailwindcss/typography": "^0.5.15",
    "lucide-react": "^0.453.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",
    "@radix-ui/react-dialog": "^1.1.7",
    "@radix-ui/react-dropdown-menu": "^2.1.7",
    "@radix-ui/react-tooltip": "^1.2.0",
    "@radix-ui/react-tabs": "^1.1.4",
    "framer-motion": "^11.18.2"
  }
}
```

### Tailwind Config
```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./client/index.html", "./client/src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "SF Pro Display", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
      },
      borderRadius: {
        lg: "1.3rem",
        md: "calc(1.3rem - 2px)",
        sm: "calc(1.3rem - 4px)",
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"), 
    require("@tailwindcss/typography")
  ],
} satisfies Config;
```

---

## Premium Component Library Recommendations

Use these premium UI libraries for Apple-quality controls:

| Library | Purpose | Why Use It |
|---------|---------|------------|
| **shadcn/ui** | Full component library | Highly customizable, Radix-based, premium defaults |
| **Radix UI** | Headless components | Accessible, unstyled primitives for custom design |
| **Framer Motion** | Animations | Smooth, physics-based animations |
| **Lucide Icons** | Icons | Clean, consistent outline icons |
| **cmdk** | Command palette | Apple Spotlight-style command menu |
| **Vaul** | Drawers | Smooth, native-feeling bottom sheets |
| **Sonner** | Toasts | Beautiful, minimal notifications |

---

## Design Checklist

Before shipping, verify your design meets these Apple-inspired standards:

### Typography
- [ ] Using Inter or SF Pro font family
- [ ] Headlines are semibold with tight tracking
- [ ] Subtitles use light weight for contrast
- [ ] Font smoothing enabled (`antialiased`)

### Colors
- [ ] Primary palette is black, white, and grays
- [ ] Borders are thin (1px) and subtle (gray-200)
- [ ] Text hierarchy uses gray scale properly
- [ ] No harsh or saturated colors

### Spacing
- [ ] Generous padding on sections (py-32 to py-48)
- [ ] Content has proper max-widths
- [ ] Consistent gap values throughout

### Controls
- [ ] Buttons are pill-shaped (`rounded-full`)
- [ ] Inputs have subtle borders and focus rings
- [ ] Cards have rounded corners (`rounded-2xl`)
- [ ] All controls have smooth transitions

### Interactions
- [ ] Hover states are subtle but noticeable
- [ ] Transitions are 200-300ms
- [ ] Lift effects on interactive cards
- [ ] Focus states are accessible

### Quality
- [ ] No default browser styling visible
- [ ] Consistent icon sizing and style
- [ ] Smooth scrollbars
- [ ] Loading states are polished

---

## Quick Start Template

```jsx
// App.tsx - Minimal Apple-style layout
export default function App() {
  return (
    <div className="min-h-screen bg-white">
      
      {/* Navbar */}
      <nav className="bg-white px-6 py-3 sticky top-0 z-50 shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-8">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="h-10" />
            <div className="w-px h-8 bg-gray-300"></div>
            <span className="text-gray-600 font-light text-xl">App Name</span>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="py-48 px-6 bg-white">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-6xl md:text-7xl font-semibold mb-8 leading-tight tracking-tight text-black">
            Your Headline
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto mb-12 leading-relaxed font-light">
            Your subtitle goes here
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
            <button className="bg-black text-white hover:bg-gray-900 font-semibold px-12 py-4 text-base rounded-full transition-all duration-300">
              Get Started
            </button>
            <button className="bg-white border-2 border-black text-black hover:bg-black hover:text-white font-semibold px-12 py-4 text-base rounded-full transition-all duration-300">
              Learn More
            </button>
          </div>
        </div>
      </section>

    </div>
  );
}
```

---

## Summary

This design system creates applications that embody Apple's design philosophy:

1. **Premium Controls** - Use shadcn/ui, Radix UI, and high-quality component libraries
2. **Minimalist Aesthetic** - Black, white, and gray palette with purposeful elements
3. **Generous Whitespace** - Large padding creates focus and elegance
4. **Refined Typography** - SF Pro/Inter with careful weight and tracking choices
5. **Subtle Interactions** - Smooth transitions that feel natural, not jarring
6. **Attention to Detail** - Every pixel matters, from scrollbars to focus rings

**The goal: Build something that looks like it belongs on apple.com**
