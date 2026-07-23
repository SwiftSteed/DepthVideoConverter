import { ReactNode } from "react";
import { StatusBar } from "./StatusBar";

interface Props {
  children: ReactNode;
}

export function AppLayout({ children }: Props) {
  return (
    <div className="min-h-screen flex flex-col">
      <StatusBar />
      <main className="flex-1 px-6 py-4">{children}</main>
    </div>
  );
}
