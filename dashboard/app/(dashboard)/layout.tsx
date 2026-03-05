import Sidebar from "@/components/Sidebar";

export default function DashboardLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <div className="flex h-screen">
            <Sidebar className="w-64 flex-shrink-0 border-r" />
            <main className="flex-1 overflow-auto bg-black">{children}</main>
        </div>
    );
}
