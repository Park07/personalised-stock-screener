function SelectInput({ id, value, onChange, placeholder, options }) {
  return (
    <select
      id={id}
      value={value}
      onChange={onChange}
      className={`w-full px-4 py-2 mt-1 bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 ${
        value === '' ? 'text-gray-400' : 'text-gray-100'
      }`}
    >
      <option value="" disabled hidden className="text-gray-400">
        {placeholder}
      </option>
      {options.map((option, index) => (
        <option key={index} value={option.value} className="text-gray-100">
          {option.label}
        </option>
      ))}
    </select>
  );
}
    
export default SelectInput;
  