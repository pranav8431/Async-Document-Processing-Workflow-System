import Link from "next/link";
import { ReactNode } from "react";

interface LayoutProps {
  title: string;
  children: ReactNode;
}

export function Layout({ title, children }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>{title}</h1>
        <nav>
          <Link href="/">Dashboard</Link>
          <Link href="/upload">Upload</Link>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
