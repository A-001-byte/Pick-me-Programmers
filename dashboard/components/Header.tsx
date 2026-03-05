export function Header() {
  return (
    <div className="bg-zinc-950 border-b border-zinc-800 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span className="text-zinc-400 font-mono">System Online</span>
          </div>
          <div className="h-3 w-px bg-zinc-700" />
          <div className="flex items-center gap-2 text-xs">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span className="text-zinc-400 font-mono">Camera Connected</span>
          </div>
          <div className="h-3 w-px bg-zinc-700" />
          <div className="flex items-center gap-2 text-xs">
            <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
            <span className="text-zinc-400 font-mono">Detection Running</span>
          </div>
        </div>
        <div className="text-xs text-zinc-500 font-mono">
          {new Date().toLocaleDateString()} {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}
