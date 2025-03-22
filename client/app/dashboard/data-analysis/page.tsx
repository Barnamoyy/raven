const Page = () => {
  return (
    <div className="flex flex-1 flex-col gap-4 p-4 w-screen h-screen">
        <h1 className="text-3xl font-bold">Data Analysis</h1>
    <div className="grid grid-cols-4 gap-4 w-full h-full">

      <div className="bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="bg-muted/50 col-span-2 p-4 rounded-xl min-h-[150px]"></div>
      <div className="bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-2 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-1 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-1 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-2 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>

      <div className="col-span-2 bg-muted/50 p-4 rounded-xl min-h-[150px]"></div>
    </div>
    </div>
  );
};

export default Page;
