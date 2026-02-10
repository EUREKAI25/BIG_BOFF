import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Suspense } from 'react';
import HomePage from './pages/HomePage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import SettingsPage from './pages/SettingsPage';
import CreatePage from './pages/CreatePage';
import PreviewPage from './pages/PreviewPage';
import ViewerPage from './pages/ViewerPage';
import GiftPage from './pages/GiftPage';
import ReceivedPage from './pages/ReceivedPage';
import LoadingScreen from './components/LoadingScreen';

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
        <div className="min-h-screen min-h-[100dvh] safe-area-inset">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/create" element={<CreatePage />} />
            <Route path="/create/:parentGiftId" element={<CreatePage />} />
            <Route path="/preview/:giftId" element={<PreviewPage />} />
            <Route path="/view/:giftId" element={<ViewerPage />} />
            <Route path="/gift/:code" element={<GiftPage />} />
            <Route path="/l/:code" element={<ReceivedPage />} />
          </Routes>
        </div>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
