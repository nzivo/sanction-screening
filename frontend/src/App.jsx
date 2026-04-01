import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useLocation,
} from "react-router-dom";
import {
  LayoutDashboard,
  Search,
  ListChecks,
  Users,
  Building2,
  MapPin,
  Menu,
} from "lucide-react";
import Dashboard from "./components/Dashboard";
import Screening from "./components/Screening";
import ListsManagement from "./components/ListsManagement";
import PEPManagement from "./components/PEPManagement";
import WorldBank from "./components/WorldBank";
import FRCKenya from "./components/FRCKenya";

function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: "/", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/screening", icon: Search, label: "Screening" },
    { path: "/lists", icon: ListChecks, label: "Lists Management" },
    { path: "/pep", icon: Users, label: "PEP Lists" },
    { path: "/worldbank", icon: Building2, label: "World Bank" },
    { path: "/frc-kenya", icon: MapPin, label: "FRC Kenya" },
  ];

  const [sidebarOpen, setSidebarOpen] = React.useState(true);

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside
        className={`${sidebarOpen ? "w-64" : "w-20"} bg-gradient-to-b from-primary-800 to-primary-900 text-white transition-all duration-300 ease-in-out`}
      >
        <div className="p-4 flex items-center justify-between">
          <h1 className={`font-bold text-xl ${!sidebarOpen && "hidden"}`}>
            Sanctions Screen
          </h1>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 hover:bg-primary-700 rounded-lg transition-colors"
          >
            <Menu size={24} />
          </button>
        </div>

        <nav className="mt-8">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-3 transition-colors ${
                  isActive
                    ? "bg-primary-600 border-l-4 border-white"
                    : "hover:bg-primary-700"
                }`}
              >
                <Icon size={24} />
                <span className={`font-medium ${!sidebarOpen && "hidden"}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/screening" element={<Screening />} />
            <Route path="/lists" element={<ListsManagement />} />
            <Route path="/pep" element={<PEPManagement />} />
            <Route path="/worldbank" element={<WorldBank />} />
            <Route path="/frc-kenya" element={<FRCKenya />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Navigation />
    </Router>
  );
}

export default App;
