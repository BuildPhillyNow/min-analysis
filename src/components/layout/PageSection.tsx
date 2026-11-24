interface PageSectionProps {
  heading?: string;
  subheading?: string;
  children: React.ReactNode;
  background?: "white" | "cream";
  id?: string;
}

export const PageSection = ({
  heading,
  subheading,
  children,
  background = "white",
  id,
}: PageSectionProps) => (
  <section
    id={id}
    className={`py-12 md:py-16 ${
      background === "cream" ? "bg-bpn-cream" : "bg-white"
    }`}
  >
    <div className="max-w-5xl mx-auto px-4">
      {heading && (
        <div className="mb-8">
          <h2 className="font-(family-name:--font-display) font-bold text-2xl md:text-3xl text-gray-900">
            {heading}
          </h2>
          {subheading && (
            <p className="mt-2 text-gray-600 text-lg">{subheading}</p>
          )}
        </div>
      )}
      {children}
    </div>
  </section>
);
