import React from 'react';

interface ThemeToggleProps {
  theme: 'light' | 'dark';
  onToggle: () => void;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ theme, onToggle }) => (
  <button
    onClick={onToggle}
    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 ${
      theme === 'dark' ? 'bg-blue-600' : 'bg-gray-300'
    }`}
    aria-label="Cambia tema"
    title={theme === 'dark' ? 'Passa al tema chiaro' : 'Passa al tema scuro'}
  >
    <span
      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200 ${
        theme === 'dark' ? 'translate-x-6' : 'translate-x-1'
      }`}
    />
    <span className="sr-only">{theme === 'dark' ? '🌙' : '☀️'}</span>
  </button>
);

export default ThemeToggle;
