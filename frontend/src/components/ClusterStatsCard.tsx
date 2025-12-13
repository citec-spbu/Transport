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
