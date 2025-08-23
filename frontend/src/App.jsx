import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Login from './pages/Login';
import AuthGuard from './components/AuthGuard';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route 
          path="/" 
          element={
            <AuthGuard>
              <Dashboard />
            </AuthGuard>
          }
        />
        <Route 
          path="/settings" 
          element={
            <AuthGuard>
              <Settings />
            </AuthGuard>
          }
        />
        {/* Add other protected routes here */}
      </Routes>
    </Router>
  );
}

export default App;