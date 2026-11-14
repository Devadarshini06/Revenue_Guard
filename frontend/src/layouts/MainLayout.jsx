import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

export default function MainLayout({
  activeTab,
  setActiveTab,
  filters,
  setFilters,
  filterOptions,
  onRefresh,
  isRefreshing,
  children
}) {
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#FAF9F6] flex">
      {/* 1. Left Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        {/* 2. Top Navigation Bar */}
        <Navbar
          filters={filters}
          setFilters={setFilters}
          filterOptions={filterOptions}
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
          setIsMobileOpen={setIsMobileOpen}
        />

        {/* 3. Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
