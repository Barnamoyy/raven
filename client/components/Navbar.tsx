
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

const Navbar = () => {
    return (
        <div className="wrapper w-full h-fit p-[30px]">
            <div className="flex flex-row justify-end items-center">
                <Avatar className="w-[36px] h-[36px]">
                    <AvatarImage src="https://github.com/shadcn.png" />
                    <AvatarFallback>CN</AvatarFallback>
                </Avatar>
            </div>
        </div>
    );
}

export default Navbar;