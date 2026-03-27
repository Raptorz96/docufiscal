import React from 'react';

interface ThemeToggleProps {
  theme: 'light' | 'dark';
  onToggle: () => void;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, onToggle }) => (
  <button
    onClick={onToggle}
    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-slate-600 dark:text-gray-300 hover:bg-slate-100 dark:hover:bg-gray-700 transition-colors"
    aria-label="Cambia tema"
    title={theme === 'dark' ? 'Passa al tema chiaro' : 'Passa al tema scuro'}
  >
    {theme === 'dark' ? (
      /* Sun icon */
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M12 7a5 5 0 100 10A5 5 0 0012 7z" />
      </svg>
    ) : (
      /* Moon icon */
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
      </svg>
    )}
  </button>
);

export default ThemeToggle;
