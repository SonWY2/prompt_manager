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
  const baseStyles = "btn";
  
  const variantStyles = {
    default: "btn-secondary",
    primary: "btn-primary",
    success: "btn-success",
    danger: "btn-danger",
    outline: "btn-secondary"
  };
  
  const sizeStyles = {
    small: "btn-sm",
    medium: "btn-md",
    large: "btn-lg"
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
