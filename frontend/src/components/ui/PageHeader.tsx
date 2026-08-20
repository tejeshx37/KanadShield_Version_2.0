export function PageHeader({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-8 pt-2">
      <h1 className="font-serif text-3xl font-bold text-ink">{title}</h1>
      {description && <p className="mt-1.5 text-ink-muted">{description}</p>}
    </div>
  );
}
