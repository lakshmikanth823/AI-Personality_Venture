import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { ChatPage } from './pages/ChatPage';
import { ApprovalConsolePage } from './pages/ApprovalConsolePage';
import { ContentLibraryPage } from './pages/ContentLibraryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { MonetizationPage } from './pages/MonetizationPage';
import { AdminConsolePage } from './pages/AdminConsolePage';
import { api } from './services/api';

export function App() {
  const [currentPage, setCurrentPage] = useState<string>('landing');
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [killSwitchActive, setKillSwitchActive] = useState<boolean>(false);

  const refreshUser = async () => {
    try {
      const user = await api.getMe();
      setCurrentUser(user);
    } catch {
      setCurrentUser(null);
    }
  };

  const refreshKillSwitch = async () => {
    try {
      const res = await api.getKillSwitchStatus();
      setKillSwitchActive(Boolean(res?.is_active));
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    refreshUser();
    refreshKillSwitch();
    // Periodically poll kill switch state for immediate safety sync
    const interval = setInterval(refreshKillSwitch, 10000);
    return () => clearInterval(interval);
  }, []);

  const renderContent = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onNavigate={setCurrentPage} />;
      case 'chat':
        return <ChatPage currentUser={currentUser} onRefreshUser={refreshUser} />;
      case 'approval':
        return <ApprovalConsolePage />;
      case 'content':
        return <ContentLibraryPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'experiments':
        return <ExperimentsPage />;
      case 'pricing':
        return <MonetizationPage currentUser={currentUser} onRefreshUser={refreshUser} />;
      case 'admin':
        return (
          <AdminConsolePage
            currentUser={currentUser}
            killSwitchActive={killSwitchActive}
            onRefreshKillSwitch={refreshKillSwitch}
          />
        );
      default:
        return <LandingPage onNavigate={setCurrentPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0b0e] text-slate-100 flex flex-col font-sans">
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        currentUser={currentUser}
        killSwitchActive={killSwitchActive}
        onRefreshUser={refreshUser}
      />
      <main className="flex-1">{renderContent()}</main>
    </div>
  );
}

export default App;
