<template>
  <div id="app" class="h-screen" data-theme="light">
    <router-view />
  </div>
</template>

<script setup lang="ts">
// Global app component
</script>

<style>
/* Design System CSS Variables - n8n/Dify Style */
:root {
  /* Dark Theme Tokens */
  --bg-base: #1F1F23;
  --bg-surface: #26262C;
  --bg-elevated: #2D2D35;
  
  --card-bg: #26262C;
  --card-border: #3A3A42;
  --card-hover: #2D2D35;
  
  --text-primary: #FFFFFF;
  --text-secondary: #A1A1AA;
  --text-muted: #71717A;
  
  --primary: #3B82F6;
  --primary-hover: #2563EB;
  --primary-light: rgba(59, 130, 246, 0.1);
  
  --danger: #EF4444;
  --warning: #F97316;
  --success: #22C55E;
  --info: #8B5CF6;
  
  --border-default: #3A3A42;
  --border-subtle: #27272A;
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 2px 6px rgba(0, 0, 0, 0.25);
  --shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-xl: 0 8px 24px rgba(0, 0, 0, 0.5);
  
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  
  --line-height-tight: 1.25;
  --line-height-normal: 1.4;
  --line-height-relaxed: 1.6;
  
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}

/* Light Theme Override - Updated per PRD v4.0 */
[data-theme="light"] {
  --bg-base: #F8F9FC;
  --bg-surface: #FFFFFF;
  --bg-elevated: #FFFFFF;
  
  --card-bg: #FFFFFF;
  --card-border: #E4E4E7;
  --card-hover: #F9F9FB;
  
  --text-primary: #1F2937;
  --text-secondary: #52525B;
  --text-muted: #A1A1AA;
  
  --primary: #2563EB;
  --primary-hover: #1D4ED8;
  --primary-light: rgba(37, 99, 235, 0.1);
  
  --danger: #F87171;
  --warning: #FB923C;
  --success: #34D399;
  --info: #60A5FA;
  
  --border-default: #E4E4E7;
  --border-subtle: #F4F4F5;
  --grid-line: rgba(0,0,0,0.05);
  
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 2px 6px rgba(16, 24, 40, 0.08);
  --shadow-lg: 0 4px 12px rgba(16, 24, 40, 0.12);
  --shadow-xl: 0 8px 24px rgba(16, 24, 40, 0.15);
}

#app {
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
  font-weight: var(--font-weight-normal);
  letter-spacing: -0.01em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  
  background-color: var(--bg-base);
  color: var(--text-primary);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  overflow: hidden;
  background-color: var(--bg-base);
}

/* Global Utility Classes */
.bg-base { background-color: var(--bg-base); }
.bg-surface { background-color: var(--bg-surface); }
.bg-elevated { background-color: var(--bg-elevated); }
.bg-card { background-color: var(--card-bg); }

.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }

.border-default { border-color: var(--border-default); }
.border-subtle { border-color: var(--border-subtle); }

.shadow-node { box-shadow: var(--shadow-md); }
.shadow-elevated { box-shadow: var(--shadow-lg); }

.rounded-node { border-radius: var(--radius-lg); }
.rounded-panel { border-radius: var(--radius-md); }

/* Enhanced Transitions & Animations */
.transition-smooth {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.transition-bounce {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.transition-elastic {
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

/* Fade animations */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* Animation classes */
.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}

.animate-slide-in {
  animation: slideIn 0.3s ease-out;
}

.animate-scale-in {
  animation: scaleIn 0.2s ease-out;
}

/* Stagger animations for lists */
.animate-stagger > * {
  animation: fadeIn 0.3s ease-out;
}

.animate-stagger > *:nth-child(1) { animation-delay: 0.1s; }
.animate-stagger > *:nth-child(2) { animation-delay: 0.2s; }
.animate-stagger > *:nth-child(3) { animation-delay: 0.3s; }
.animate-stagger > *:nth-child(4) { animation-delay: 0.4s; }
.animate-stagger > *:nth-child(5) { animation-delay: 0.5s; }

/* Floating animation */
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-6px);
  }
}

.animate-float {
  animation: float 3s ease-in-out infinite;
}

/* Pulse glow effect */
@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 5px var(--primary-light);
  }
  50% {
    box-shadow: 0 0 20px var(--primary-light), 0 0 30px var(--primary-light);
  }
}

.animate-pulse-glow {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* Enhanced Focus Ring */
.focus-ring:focus {
  outline: none;
  box-shadow: 0 0 0 2px var(--primary-light), 0 0 0 4px var(--primary);
  transition: box-shadow 0.2s ease;
}

/* Interactive states */
.interactive {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.interactive:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.interactive:active {
  transform: translateY(0);
  transition: all 0.1s ease;
}

/* Backdrop blur effects */
.backdrop-blur {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.backdrop-blur-lg {
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

/* Scrollbar Styling */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-surface);
}

::-webkit-scrollbar-thumb {
  background: var(--border-default);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
  
  .animate-float,
  .animate-pulse-glow {
    animation: none;
  }
}
</style>