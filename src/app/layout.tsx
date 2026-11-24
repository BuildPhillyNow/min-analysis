import type { Metadata } from "next";
import { Outfit, DM_Sans } from "next/font/google";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "600", "700", "800", "900"],
  variable: "--font-outfit",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-dm-sans",
});

export const metadata: Metadata = {
  title: "The MIN Overlay: A Parcel-Level Impact Analysis | Build Philly Now",
  description:
    "Philadelphia's Mixed-Income Neighborhoods overlay has produced 19 affordable units in four years. Over the same period, housing project starts inside it fell 61%, against 47% in comparable parts of the city, and 79% in its West Philadelphia half. An analysis by Build Philly Now.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${outfit.variable} ${dmSans.variable}`}>
      <body className="font-(family-name:--font-body) bg-white text-gray-900 antialiased">
        <SiteHeader />
        <main className="min-h-screen">{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
