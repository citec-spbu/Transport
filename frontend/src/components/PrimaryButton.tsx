import React from "react";

type PrimaryButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  children: React.ReactNode;
};

export default function PrimaryButton({ children, className = "", ...rest }: PrimaryButtonProps) {
  return (
    <button
      {...rest}
      className={`
        px-6 py-3 rounded-4xl font-medium text-sm transition-all duration-200
        hover:bg-[#003A8C] hover:text-white border hover:border-[#003A8C]
        bg-transparent text-[#003A8C] border-[#003A8C]
        active:scale-[0.97]
        ${className}
      `}
    >
      {children}
    </button>
  );
}
