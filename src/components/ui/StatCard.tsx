interface StatCardProps {
  value: string;
  label: string;
  detail?: string;
}

export const StatCard = ({ value, label, detail }: StatCardProps) => (
  <div className="bg-bpn-card rounded-xl p-6 text-center">
    <div className="font-(family-name:--font-display) font-black text-3xl md:text-4xl text-bpn-green">
      {value}
    </div>
    <div className="mt-1 font-semibold text-gray-900 text-sm uppercase tracking-wide">
      {label}
    </div>
    {detail && <div className="mt-1 text-gray-500 text-xs">{detail}</div>}
  </div>
);
