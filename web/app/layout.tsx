import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GroundedGate",
  description: "Evidence grounded answers with visible validation gates",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
