import Sidebar from "@/components/layout/Sidebar";
import LoadingGate from "@/components/layout/LoadingGate";
import { WellsProvider } from "@/lib/wells-store";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <WellsProvider>
      <div className="flex h-screen overflow-hidden bg-[#f8f7f2]">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="p-6 max-w-screen-2xl mx-auto h-full">
            <LoadingGate>{children}</LoadingGate>
          </div>
        </main>
      </div>
    </WellsProvider>
  );
}
