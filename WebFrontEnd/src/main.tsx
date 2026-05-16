
  import { createRoot } from "react-dom/client";
  import App from "./App.tsx";
  import "./index.css";
  import BuyerDashboard from './components/BuyerDashboard';
  import { BrowserRouter,Route,Routes } from 'react-router-dom'
  import Test from "./components/Test.tsx";
  import LoginTest from "./components/LoginTest.tsx";
import SellerDashboard from "./components/SellerDashboard.tsx";
import AdminDashboard from "./components/AdminDashboard.tsx";
  createRoot(document.getElementById("root")!).render(
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/buyer-dashboard" element={<BuyerDashboard />} />
        <Route path="/seller-dashboard" element={<SellerDashboard />} />
        <Route path="/admin-dashboard" element={<AdminDashboard />} />
        
        <Route path = "/connect-facebook" element={<Test />} />
        <Route path = "/test-login" element = {<LoginTest/>} />
      </Routes>
    </BrowserRouter>
    
);
  
