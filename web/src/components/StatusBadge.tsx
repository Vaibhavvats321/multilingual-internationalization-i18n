export type StatusTone = 'ok' | 'degraded' | 'unavailable';

export interface StatusBadgeProps {
  readonly tone: StatusTone;
  readonly label: string;
}

const toneClasses: Readonly<Record<StatusTone, string>> = {
  ok: 'bg-emerald-100 text-emerald-900',
  degraded: 'bg-amber-100 text-amber-900',
  unavailable: 'bg-red-100 text-red-900'
};

/**
 * Small presentational badge used to show the state of a service or a
 * dependency. It carries the tone in `data-tone` so tests and stylesheets
 * do not depend on the class names.
 */
export function StatusBadge({tone, label}: StatusBadgeProps) {
  return (
    <span
      data-tone={tone}
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${toneClasses[tone]}`}
    >
      {label}
    </span>
  );
}
