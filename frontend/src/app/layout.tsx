import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Adaptive Financial Twin | Autonomous Financial Intelligence",
  description: "A living, stateful digital twin of your financial life powered by stochastic simulations and behavioral constraints.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-[#070b14] text-slate-100">
        {children}
      </body>
    </html>
  );
}
