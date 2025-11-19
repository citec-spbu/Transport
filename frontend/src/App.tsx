import { Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Clustering from "./pages/Clustering";
import Parameters from "./pages/Parameters";
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/parameters" element={<Parameters/>}/>
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/clustering" element={<Clustering />} />
    </Routes>
  );
}
