interface PageHeroProps {
  title: string;
  subtitle: string;
  stat?: { value: string; label: string };
}

export const PageHero = ({ title, subtitle, stat }: PageHeroProps) => (
  <section className="bg-bpn-dark text-white py-16 md:py-20">
    <div className="max-w-5xl mx-auto px-4">
      <h1 className="font-(family-name:--font-display) font-black text-3xl md:text-5xl uppercase tracking-tight leading-tight">
        {title}
      </h1>
      <p className="mt-4 text-gray-300 text-lg md:text-xl max-w-3xl">
        {subtitle}
      </p>
      {stat && (
        <div className="mt-8 inline-flex items-baseline gap-3 bg-white/10 rounded-xl px-6 py-4">
          <span className="font-(family-name:--font-display) font-black text-4xl md:text-5xl text-bpn-green">
            {stat.value}
          </span>
          <span className="text-gray-300 text-sm md:text-base">
            {stat.label}
          </span>
        </div>
      )}
    </div>
  </section>
);
