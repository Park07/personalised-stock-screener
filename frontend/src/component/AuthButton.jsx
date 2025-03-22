function AuthButton({ type = 'button', children, onClick, className = '' }) {
    return (
      <button
        type={type}
        onClick={onClick}
        className={`w-full px-4 py-2 text-white bg-gray-800 rounded-md hover:bg-gray-600 focus:outline-none focus:bg-gray-500 ${className}`}
      >
        {children}
      </button>
    );
  }
  
  export default AuthButton;