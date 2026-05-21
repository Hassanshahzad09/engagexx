import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Moon, Sun } from 'lucide-react';
import LandingPage from './components/LandingPage';
import BuyerDashboard from './components/BuyerDashboard';
import SellerDashboard from './components/SellerDashboard';
import AdminDashboard from './components/AdminDashboard';
import LoginSignup from './components/LoginSignup';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

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

  const [currentPage, setCurrentPage] = useState(() => getPageFromPath(window.location.pathname));
  const [currentUser, setCurrentUser] = useState(location.state?.userData || null);
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'light');

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark'));
  };

  const goToPage = (page) => {
    setCurrentPage(page);
    navigate(getPathFromPage(page), currentUser ? { state: { userData: currentUser } } : undefined);
  };

  useEffect(() => {
    const routeUser = location.state?.userData || null;
    const activeUser = routeUser || currentUser;
    const requestedPage = getPageFromPath(location.pathname);
    const isProtectedPage = requestedPage === 'buyer' || requestedPage === 'seller' || requestedPage === 'admin';

    if (routeUser && routeUser !== currentUser) {
      setCurrentUser(routeUser);
    }

    if (isProtectedPage && !activeUser) {
      setCurrentPage('login');
      navigate('/login', { replace: true });
      return;
    }

    setCurrentPage(requestedPage);
  }, [location.pathname, location.state, currentUser, navigate]);

  const handleLogin = (userData) => {
    const page = getPageFromUser(userData);
    setCurrentUser(userData);
    setCurrentPage(page);
    navigate(getPathFromPage(page), { replace: true, state: { userData } });
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setCurrentPage('landing');
    navigate('/', { replace: true });
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'landing':
        return <LandingPage onNavigate={goToPage} />;
      case 'buyer':
        return <BuyerDashboard userData={currentUser} onNavigate={goToPage} onLogout={handleLogout} />;
      case 'seller':
        return <SellerDashboard userData={currentUser} onNavigate={goToPage} onLogout={handleLogout} theme={theme} />;
      case 'admin':
        return <AdminDashboard userData={currentUser} onNavigate={goToPage} onLogout={handleLogout} />;
      case 'login':
        return <LoginSignup onLogin={handleLogin} onBack={() => goToPage('landing')} />;
      default:
        return <LandingPage onNavigate={goToPage} />;
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <button
        type="button"
        className="theme-toggle"
        onClick={toggleTheme}
        aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
      </button>
      {renderPage()}
    </div>
  );
}
