import Card from "./ui/Card";

interface ClusterStatistics {
  modularity?: number | null;
  silhouette?: number | null;
  conductance?: number | null;
  coverage?: number | null;
}

interface Props {
  stats?: ClusterStatistics;
}

const format = (value?: number | null, invert = false) => {
  if (value == null) return "—";

  const v = invert ? 1 - value : value;

  return v.toFixed(2);
};

/**
 * Render a card displaying cluster quality metrics.
 *
 * Renders four labeled rows for modularity, silhouette coefficient, conductance, and coverage; each value is formatted for display. If `stats` is not provided, nothing is rendered.
 *
 * @param stats - Optional cluster metrics object with numeric or `null` fields: `modularity`, `silhouette`, `conductance`, and `coverage`.
 * @returns A JSX element containing the metrics card, or `null` when `stats` is falsy.
 */
export default function ClusterStatsCard({ stats }: Props) {
  if (!stats) {
    return null;
  }
  return (
    <Card className="p-3 space-y-2">
      <div className="text-xs font-semibold text-gray-800">
        Качество кластеризации
      </div>

      <StatRow
        label="Модулярность"
        value={format(stats.modularity)}
        hint="Чем выше тем лучше"
      />

      <StatRow
        label="Силуэтный коэффициент"
        value={format(stats.silhouette)}
        hint="Чем выше тем лучше"
      />

      <StatRow
        label="Проводимость"
        value={format(stats.conductance)}
        hint="Чем ниже тем лучше"
      />

      <StatRow
        label="Покрытие"
        value={format(stats.coverage)}
        hint="Чем выше тем лучше"
      />
    </Card>
  );
}

/**
 * Renders a single horizontal row with a left-aligned label and a right-aligned value.
 *
 * @param label - The text shown on the left side of the row.
 * @param value - The text shown on the right side of the row, styled prominently.
 * @param hint - Optional hint text associated with the value; accepted but not currently rendered.
 * @returns A JSX element containing the styled label/value row.
 */
function StatRow({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="flex justify-between items-center text-[11px]">
      <div className="text-gray-600">{label}</div>

      <div className="flex items-center gap-2">
        <span className="text-gray-900 font-medium">{value}</span>
        {/* <span className="text-gray-400 text-[10px]">{hint}</span> */}
      </div>
    </div>
  );
}