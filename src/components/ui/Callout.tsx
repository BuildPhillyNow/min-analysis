interface CalloutProps {
  variant?: "info" | "warning" | "success";
  title?: string;
  children: React.ReactNode;
}

const VARIANT_STYLES = {
  info: "bg-blue-50 border-blue-300 text-blue-900",
  warning: "bg-red-50 border-scenario-danger text-red-900",
  success: "bg-green-50 border-bpn-green text-green-900",
};

export const Callout = ({
  variant = "info",
  title,
  children,
}: CalloutProps) => (
  <div className={`rounded-xl border-l-4 p-5 ${VARIANT_STYLES[variant]}`}>
    {title && (
      <p className="font-(family-name:--font-display) font-bold text-lg mb-1">
        {title}
      </p>
    )}
    <div className="text-sm leading-relaxed">{children}</div>
  </div>
);
