export default function Header() {
  return (
    <header className="border-b border-slate-700/50 bg-navy-800/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/40 flex items-center justify-center">
            <span className="text-blue-400 text-sm font-bold">M</span>
          </div>
          <div>
            <h1 className="text-white font-semibold text-lg leading-none">MedInsight</h1>
            <p className="text-slate-500 text-xs mt-0.5">Clinical Document Intelligence</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-slate-400 text-sm">API Live</span>
        </div>
      </div>
    </header>
  );
}
