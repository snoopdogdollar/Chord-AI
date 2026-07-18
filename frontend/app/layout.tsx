import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "ChordAI",
  description: "Generate rehearsal-ready chord sheets from audio."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
