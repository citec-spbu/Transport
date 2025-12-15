import Card from "./ui/Card";

interface ClusterMetrics {
  num_communities?: number | null;
  min_size?: number | null;
  max_size?: number | null;
  mean_size?: number | null;
  median_size?: number | null;
  std_size?: number | null;
}

interface Props {
  stats?: ClusterMetrics | null;
}

const format = (value?: number | null, digits = 2) => {
  if (value == null) return "—";
  return value.toFixed(digits);
};

export default function ClusterInfoCard({ stats }: Props) {
  if (!stats) return null;

  return (
    <Card className="p-3 space-y-2">
      <div className="text-xs font-semibold text-gray-800">
        Распределение размеров кластеров
      </div>

      <StatRow
        label="Количество кластеров"
        value={format(stats.num_communities, 0)}
      />
      <StatRow label="Мин. размер" value={format(stats.min_size, 0)} />
      <StatRow label="Макс. размер" value={format(stats.max_size, 0)} />
      <StatRow label="Средний размер" value={format(stats.mean_size, 2)} />
      <StatRow label="Медиана" value={format(stats.median_size, 0)} />
      <StatRow label="Станд. отклонение" value={format(stats.std_size, 2)} />
    </Card>
  );
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center text-[11px]">
      <span className="text-gray-600">{label}</span>
      <span className="text-gray-900 font-medium">{value}</span>
    </div>
  );
}
