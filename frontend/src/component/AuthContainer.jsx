function AuthContainer({ children }) {
    return (
      <div className="flex items-start justify-center bg-background pt-16">
        <div className="w-full max-w-md p-8 space-y-4 bg-nav rounded-lg shadow-md">
          {children}
        </div>
      </div>
    );
  }
  
  export default AuthContainer;