import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface LayoutProps {
  onTriggerRun: () => void;
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({
  onTriggerRun,
  children,
}) => {
  return (
    <div className="flex min-h-screen bg-[#f8fafc] text-[#0f172a] font-sans selection:bg-[#8b5cf6] selection:text-[#ffffff]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header onTriggerRun={onTriggerRun} />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
};
