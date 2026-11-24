import Link from "next/link";

interface CTABannerProps {
  heading?: string;
  text?: string;
  buttonText?: string;
  href?: string;
}

export const CTABanner = ({
  heading = "Make Your Voice Heard",
  text = "Show your Council member the data. Philadelphia needs stronger transit-oriented zoning.",
  buttonText = "See Your District",
  href = "/council-districts/",
}: CTABannerProps) => (
  <section className="bg-bpn-green py-12">
    <div className="max-w-5xl mx-auto px-4 text-center">
      <h2 className="font-(family-name:--font-display) font-bold text-2xl md:text-3xl text-white">
        {heading}
      </h2>
      <p className="mt-3 text-white/90 text-lg max-w-2xl mx-auto">{text}</p>
      <Link
        href={href}
        className="mt-6 inline-block bg-white text-bpn-green px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
      >
        {buttonText}
      </Link>
    </div>
  </section>
);
