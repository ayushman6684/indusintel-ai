export default function Navbar({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="h-16 border-b border-line flex items-center justify-between px-8 shrink-0">
      <div>
        <h1 className="font-display text-[17px] font-semibold text-ink tracking-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="text-xs text-ink-muted mt-0.5">{subtitle}</p>
        )}
      </div>
      {action}
    </header>
  );
}
