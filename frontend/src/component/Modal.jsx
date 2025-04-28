import AuthButton from "./AuthButton";
import Carousel from "./Carousel";

const Modal = ({ onClose, ticker }) => {
  return (
    <div className="fixed inset-0 bg-nav z-50 flex flex-col gap-4 items-center p-8">
      <button onClick={onClose} className="absolute top-2 right-2 text-5xl text-gray-600 hover:text-black">×</button>
      <div className="w-full flex-1 p-4">
        <Carousel ticker={ticker}/>
      </div>
      <div className="w-full flex-col flex flex-1 p-4 gap-4">
        <span className="text-white font-bold">Risk Tolerance</span>
        <div className="flex gap-4 flex-1">
          <AuthButton
            type="submit" 
            className="w-full flex justify-center items-center"
          >Conservative</AuthButton>
          <AuthButton
            type="submit"
            className="w-full flex justify-center items-center"
          >Moderate</AuthButton>
          <AuthButton
            type="submit"
            className="w-full flex justify-center items-center"
          >Aggressive</AuthButton>
        </div>
        <span className="text-white font-bold">Investment Goal</span>
        <div className="flex gap-4 flex-1">
          <AuthButton
            type="submit"
            className="w-full flex justify-center items-center"
          >Income</AuthButton>
          <AuthButton
            type="submit"
            className="w-full flex justify-center items-center"
          >Balanced</AuthButton>
          <AuthButton
            type="submit"
            className="w-full flex justify-center items-center"
          >Growth</AuthButton>
        </div>
      </div>

      <div className="w-full flex-1 flex  text-center items-center justify-center">
        <h2 className="text-4xl">Other stuff</h2>
      </div>
    </div>
  );
};
  
  export default Modal;