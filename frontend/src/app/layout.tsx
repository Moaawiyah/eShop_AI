import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import type { ReactNode } from "react";

import { ThemeProvider } from "@/components/layout/theme-provider";

import "./globals.css";

// next/font downloads and self-hosts the font at build time; the browser
// makes no request to Google at runtime.
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: { default: "eShop_AI", template: "%s · eShop_AI" },
  description:
    "eShop_AI is a portfolio demo of a cloud-native, AI-assisted electronics storefront. All payments are simulated.",
};

export const viewport: Viewport = {
  colorScheme: "light dark",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // suppressHydrationWarning: next-themes sets the theme class before hydration.
    <html lang="en" className={geistSans.variable} suppressHydrationWarning>
      <body className="min-h-dvh">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
