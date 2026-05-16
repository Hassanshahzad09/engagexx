
  import { createRoot } from "react-dom/client";
  import App from "./App.tsx";
  import "./index.css";
  import { BrowserRouter,Route,Routes } from 'react-router-dom'
  createRoot(document.getElementById("root")!).render(
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/login" element={<App />} />
        <Route path="/buyer-dashboard" element={<App />} />
        <Route path="/seller-dashboard" element={<App />} />
        <Route path="/admin-dashboard" element={<App />} />
      </Routes>
    </BrowserRouter>
    
);
  
