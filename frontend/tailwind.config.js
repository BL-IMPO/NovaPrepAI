/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./*.html",
    "./src/**/*.{html,js}",
    "./assets/js/**/*.js"
  ],
  safelist: [
    // Sidebar active/state classes
    'bg-primary', 'text-primary-content', 'border-primary', 'shadow-primary/30',
    'bg-success/15', 'text-success', 'border-success/30',
    'bg-warning/15', 'text-warning', 'border-warning/30',

    // Answer options states
    'bg-info/10', 'text-info', 'border-info',
    'bg-base-200', 'text-base-content/60', 'hover:border-primary/40',
    'hover:-translate-y-1', 'hover:shadow-lg', 'hover:bg-base-100',
    'group-hover:bg-base-300', 'group-hover:text-base-content',
    'shadow-xl', '-translate-y-1', 'shadow-md',

    // Timer states
    'bg-error', 'text-error-content', 'animate-pulse',
    'bg-warning', 'text-warning-content',

    // Success/Fail Badges
    'badge-success', 'badge-error',

    // Loading spinners
    'loading', 'loading-spinner', 'loading-sm', 'loading-xs'
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("daisyui")
  ],
}