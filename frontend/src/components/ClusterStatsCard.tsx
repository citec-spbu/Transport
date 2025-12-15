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

      <StatRow label="Модулярность" value={format(stats.modularity)} />

      <StatRow label="Проводимость" value={format(stats.conductance)} />

      <StatRow label="Покрытие" value={format(stats.coverage)} />
    </Card>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
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
