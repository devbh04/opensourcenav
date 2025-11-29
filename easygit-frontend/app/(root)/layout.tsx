import AppBar from "@/components/shared/appbar";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <main className="text-white">
        {/* <AppBar/> */}
        {children}
    </main>
  );
}
