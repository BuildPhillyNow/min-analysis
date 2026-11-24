export const SiteFooter = () => (
  <footer className="print:hidden bg-bpn-dark text-white">
    <div className="max-w-6xl mx-auto px-4 py-12">
      <div className="flex flex-col md:flex-row items-start justify-between gap-8">
        <div>
          <img
            src="/images/BPN_Logo_White.svg"
            alt="Build Philly Now"
            className="h-8 mb-4"
          />
          <p className="text-gray-400 text-sm max-w-md">
            Data-driven analysis of Philadelphia&rsquo;s Mixed-Income
            Neighborhoods overlay and its impact on housing production.
          </p>
        </div>

        <div className="flex flex-col items-start gap-3">
          <a
            href="https://buildphillynow.org"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-300 hover:text-white transition-colors"
          >
            buildphillynow.org
          </a>
          <a
            href="https://philly-toc.netlify.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-300 hover:text-white transition-colors"
          >
            TOC Housing Yield Analysis →
          </a>
          <a
            href="https://phlcouncil.com/council-members/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-bpn-green hover:bg-bpn-green-dark text-white px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors"
          >
            Contact Your Council Member
          </a>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-gray-700 text-center text-xs text-gray-500">
        &copy; {new Date().getFullYear()} Build Philly Now. All rights
        reserved.
      </div>
    </div>
  </footer>
);
