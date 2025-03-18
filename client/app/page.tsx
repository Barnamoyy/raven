import Navbar from "@/components/Navbar";

export default function Home() {
  return (
    <div className="Outer-Wrapper w-full h-screen grid grid-cols-4">
      {/* Sidebar */}
      <div className="Sidebar col-span-1 bg-black h-screen">
        <h2 className="text-[36px] text-white px-[80px] py-[30px] font-serif font-bold">
          Sidebar
        </h2>
      </div>

      {/* Right Side (Navbar + Content) */}
      <div className="col-span-3 flex flex-col w-full h-screen">
        {/* Navbar at the top */}
        <Navbar />
        
        {/* Page Content */}
        <div className="flex-grow flex justify-start items-start px-[40px] pt-[80px]">
          <div className="leading-10">
            <h6 className="font-[12px] font-semibold">Dashboard</h6>
            <h1 className="text-[64px] font-bold font-sans w-fit h-fit">Hi, Barnamoy</h1>
          </div>
        </div>
      </div>
    </div>
  );
}
