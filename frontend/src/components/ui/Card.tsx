import React from "react";
import clsx from "clsx";

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

const Card: React.FC<CardProps> = ({ className, children, ...props }) => {
  return (
    <div
      className={clsx(
        "bg-white rounded-lg border-[1.5px] border-[#E0E6EA]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;