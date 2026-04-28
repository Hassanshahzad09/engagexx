import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import BuyerDashboard from './components/BuyerDashboard';
import SellerDashboard from './components/SellerDashboard';
import AdminDashboard from './components/AdminDashboard';
import LoginSignup from './components/LoginSignup';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const STORAGE_KEY = 'engageXUser';

  const getPageFromPath = (pathname) => {
    if (pathname === '/buyer-dashboard') return 'buyer';
    if (pathname === '/seller-dashboard') return 'seller';
    if (pathname === '/admin-dashboard') return 'admin';
    if (pathname === '/login') return 'login';
    return 'landing';
  };

  const getPageFromUser = (userData) => {
    if (userData?.isAdmin || userData?.role === 'admin') return 'admin';
    if (userData?.role === 'seller') return 'seller';
    return 'buyer';
  };

  const getPathFromPage = (page) => {
    if (page === 'buyer') return '/buyer-dashboard';
    if (page === 'seller') return '/seller-dashboard';
    if (page === 'admin') return '/admin-dashboard';
    if (page === 'login') return '/login';
    return '/';
  };

  const [currentPage, setCurrentPage] = useState(() => {
    const savedUser = localStorage.getItem(STORAGE_KEY);

    if (!savedUser) {
      return getPageFromPath(window.location.pathname);
    }

    try {
      return getPageFromUser(JSON.parse(savedUser));
    } catch (error) {
      localStorage.removeItem(STORAGE_KEY);
      return getPageFromPath(window.location.pathname);
    }
  });
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const goToPage = (page) => {
    setCurrentPage(page);
    navigate(getPathFromPage(page));
  };

  useEffect(() => {
    const savedUser = localStorage.getItem(STORAGE_KEY);

    if (!savedUser) {
      setIsLoggedIn(false);
      setCurrentPage(getPageFromPath(location.pathname));
      return;
    }

    try {
      const parsedUser = JSON.parse(savedUser);
      setIsLoggedIn(true);
      const allowedPage = getPageFromUser(parsedUser);
      const requestedPage = getPageFromPath(location.pathname);

      if (
        requestedPage === 'buyer' ||
        requestedPage === 'seller' ||
        requestedPage === 'admin'
      ) {
        if (requestedPage !== allowedPage) {
          setCurrentPage(allowedPage);
          navigate(getPathFromPage(allowedPage), { replace: true });
        } else {
          setCurrentPage(requestedPage);
        }
      } else {
        setCurrentPage(allowedPage);
        navigate(getPathFromPage(allowedPage), { replace: true });
      }
    } catch (error) {
      console.error('Session restore failed:', error);
      localStorage.removeItem(STORAGE_KEY);
      setIsLoggedIn(false);
      setCurrentPage('landing');
      navigate('/', { replace: true });
    }
  }, [location.pathname, navigate]);

  const handleLogin = (userData) => {
    setIsLoggedIn(true);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData));
    goToPage(getPageFromUser(userData));
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.removeItem(STORAGE_KEY);
    goToPage('landing');
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onNavigate={goToPage} />;
      
      case 'buyer':
        return <BuyerDashboard onNavigate={goToPage} onLogout={handleLogout} />;
      case 'seller':
        return <SellerDashboard onNavigate={goToPage} onLogout={handleLogout} />;
      case 'admin':
        return <AdminDashboard onNavigate={goToPage} onLogout={handleLogout} />;
      case 'login':
        return <LoginSignup onLogin={handleLogin} onBack={() => goToPage('landing')} />;
      default:
        return <LandingPage onNavigate={goToPage} />;
    }
  };

  return <div className="min-h-screen bg-white">{renderPage()}</div>;
}
