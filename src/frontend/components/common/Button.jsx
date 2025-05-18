import React from 'react';

// 버튼 컴포넌트
function Button({ 
  children, 
  variant = 'default', 
  size = 'medium', 
  onClick,
  className = '',
  ...props
}) {
  const baseStyles = "inline-flex items-center justify-center rounded focus:outline-none transition-colors";
  
  const variantStyles = {
    default: "bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-white",
    primary: "bg-blue-600 hover:bg-blue-700 text-white",
    success: "bg-green-600 hover:bg-green-700 text-white",
    danger: "bg-red-600 hover:bg-red-700 text-white",
    outline: "border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-800"
  };
  
  const sizeStyles = {
    small: "px-2 py-1 text-xs",
    medium: "px-3 py-2 text-sm",
    large: "px-4 py-2 text-base"
  };
  
  return (
    <button
      className={`${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </button>
  );
}

export default Button;