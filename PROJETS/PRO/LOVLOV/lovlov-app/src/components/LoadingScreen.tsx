import HeartLogo from './HeartLogo';

export default function LoadingScreen() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-love-dark">
      <div className="text-center">
        <HeartLogo className="w-24 h-24 mx-auto animate-heartbeat" />
        <p className="mt-4 text-cream/60 font-romantic text-2xl">LovLov</p>
      </div>
    </div>
  );
}
