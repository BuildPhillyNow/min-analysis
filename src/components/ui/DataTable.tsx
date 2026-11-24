interface DataTableProps {
  headers: string[];
  rows: (string | number)[][];
  caption?: string;
  highlightRow?: number;
}

export const DataTable = ({
  headers,
  rows,
  caption,
  highlightRow,
}: DataTableProps) => (
  <div className="overflow-x-auto rounded-xl border border-gray-200">
    <table className="w-full text-sm">
      {caption && (
        <caption className="px-4 py-2 text-left text-xs text-gray-500 bg-gray-50 border-b">
          {caption}
        </caption>
      )}
      <thead>
        <tr className="bg-bpn-dark text-white">
          {headers.map((h, i) => (
            <th
              key={i}
              className="px-4 py-3 text-left font-semibold text-xs uppercase tracking-wide"
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, ri) => (
          <tr
            key={ri}
            className={`border-b border-gray-100 ${
              ri === highlightRow
                ? "bg-bpn-green/10 font-semibold"
                : ri % 2 === 0
                ? "bg-white"
                : "bg-gray-50"
            }`}
          >
            {row.map((cell, ci) => (
              <td key={ci} className="px-4 py-3">
                {typeof cell === "number" ? cell.toLocaleString() : cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);
