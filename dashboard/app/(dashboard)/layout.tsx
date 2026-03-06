import Sidebar from "@/components/Sidebar";
import AuthProvider from "@/components/AuthProvider";

export default function DashboardLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <AuthProvider>
            <div className="flex h-screen">
                <Sidebar className="w-64 flex-shrink-0 border-r" />
                <main className="flex-1 overflow-auto bg-black">{children}</main>
            </div>
        </AuthProvider>
    );
}
