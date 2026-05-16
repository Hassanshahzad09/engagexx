import { useState } from 'react';
import LandingPage from './components/LandingPage';
import BuyerDashboard from './components/BuyerDashboard';
import SellerDashboard from './components/SellerDashboard';
import AdminDashboard from './components/AdminDashboard';
import LoginSignup from './components/LoginSignup';

export default function App() {
  console.log("Main App Is Running")
  const [currentPage, setCurrentPage] = useState('landing');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const handleLogin = (userType) => {
    setIsLoggedIn(true);
    if (userType === 'buyer') {
      setCurrentPage('buyer');
    } else if (userType === 'seller') {
      setCurrentPage('seller');
    } else if (userType === 'admin') {
      setCurrentPage('admin');
    } else {
      setCurrentPage('buyer');
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setCurrentPage('landing');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onNavigate={setCurrentPage} />;
      
      case 'buyer':
        return <BuyerDashboard onLogout={handleLogout} />;
      case 'seller':
        return <SellerDashboard onLogout={handleLogout} />;
      case 'admin':
        return <AdminDashboard onNavigate={setCurrentPage} onLogout={handleLogout} />;
      case 'login':
        return <LoginSignup onLogin={handleLogin} onBack={() => setCurrentPage('landing')} onLogout={handleLogout} />;
      default:
        return <LandingPage onNavigate={setCurrentPage} />;
    }
  };

  return <div className="min-h-screen bg-white">{renderPage()}</div>;
}
