function TextInput({ type = 'text', id, value, onChange, placeholder }) {
    return (
      <input
        type={type}
        id={id}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required
        className="w-full px-4 py-2 mt-1 text-gray-100 bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
    );
  }
  
  export default TextInput;