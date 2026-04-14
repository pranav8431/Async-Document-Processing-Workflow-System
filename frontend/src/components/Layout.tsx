import Link from "next/link";
import { ReactNode } from "react";

interface LayoutProps {
  title: string;
  children: ReactNode;
}

export function Layout({ title, children }: LayoutProps) {
  const demoVideoUrl = "https://www.loom.com/share/c9bae7f209f84a35925b95d0bb236b57";

  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>{title}</h1>
        <nav>
          <Link href="/">Dashboard</Link>
          <Link href="/upload">Upload</Link>
          <a href={demoVideoUrl} target="_blank" rel="noreferrer">Refer to: Loom Demo</a>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
