import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import ClickSpark from "@/components/react-bits/ClickSpark/ClickSpark";
import "./globals.css";
import { Toaster } from "sonner";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "EasyGit",
  description:
    "Simplifies a git repository into tutorials for them to understand it.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-github`}
      >
        <ClickSpark
          sparkColor="#fff"
          sparkSize={10}
          sparkRadius={15}
          sparkCount={8}
          duration={400}
        >
          <main>{children}</main>
          <Toaster/>
        </ClickSpark>
      </body>
    </html>
  );
}
