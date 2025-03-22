import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";

export default function NewLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div>
        <SidebarProvider>
          <AppSidebar />
          {children}
        </SidebarProvider>
      </div>
    </>
  );
}
