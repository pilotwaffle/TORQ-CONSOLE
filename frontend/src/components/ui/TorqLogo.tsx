import React from 'react';

interface TorqLogoProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const TorqLogo: React.FC<TorqLogoProps> = ({
  size = 'md',
  className = ''
}) => {
  const sizeMap = {
    sm: 24,
    md: 32,
    lg: 48,
  };

  const dimension = sizeMap[size];

  return (
    <svg
      width={dimension}
      height={dimension}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="TORQ Console"
    >
      {/* Outer ring - TORQ Blue */}
      <circle
        cx="16"
        cy="16"
        r="14"
        stroke="#0078d4"
        strokeWidth="2"
        fill="none"
      />

      {/* Inner hexagon - TORQ Green accent */}
      <path
        d="M16 6 L24 11 L24 21 L16 26 L8 21 L8 11 Z"
        stroke="#10b981"
        strokeWidth="1.5"
        fill="none"
        strokeLinejoin="round"
      />

      {/* Center T shape - TORQ Accent Blue */}
      <path
        d="M12 13 L20 13 M16 13 L16 22"
        stroke="#0086f0"
        strokeWidth="2.5"
        strokeLinecap="round"
      />

      {/* Accent dots - TORQ Orange */}
      <circle cx="16" cy="16" r="1.5" fill="#f59e0b" />
      <circle cx="12" cy="12" r="1" fill="#f59e0b" opacity="0.6" />
      <circle cx="20" cy="12" r="1" fill="#f59e0b" opacity="0.6" />
    </svg>
  );
};
