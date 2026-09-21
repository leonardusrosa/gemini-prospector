import type { Metadata } from "next";
import "./globals.css";
import { assetPath } from "@/lib/site-paths";

export const metadata: Metadata = {
  title: "Dallas Detailing And Buffing | Auto Detailing & Paint Correction | Addison TX",
  description: "Paint correction, buffing, and full auto detailing by Wilson in Addison, Texas. Backed by a 4.9 rating across 268 public reviews.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <meta name="robots" content="noindex, nofollow" />
        <link rel="icon" href={assetPath("favicon.svg")} type="image/svg+xml" />
        <link
          rel="preload"
          as="image"
          href={assetPath("hero-poster.webp")}
          type="image/webp"
          fetchPriority="high"
        />
      </head>
      <body className="bg-[#08090b] text-[#f0f2f5] antialiased overflow-x-hidden selection:bg-[#caa35d] selection:text-[#08090b]">
        {children}
      </body>
    </html>
  );
}
