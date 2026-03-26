import styles from "./DataTable.module.css";

interface DataTableProps {
  data: Record<string, unknown>[];
  maxRows?: number;
}

export default function DataTable({ data, maxRows }: DataTableProps) {
  if (!data || data.length === 0) {
    return <p className={styles.empty}>No data available</p>;
  }

  const rows = maxRows ? data.slice(0, maxRows) : data;
  const cols = Object.keys(data[0]);

  const formatVal = (v: unknown) => {
    if (v === null || v === undefined) return "—";
    if (typeof v === "number") {
      if (Math.abs(v) > 999) return v.toLocaleString(undefined, { maximumFractionDigits: 2 });
      return typeof v === "number" ? v.toFixed(2).replace(/\.00$/, "") : String(v);
    }
    return String(v);
  };

  const getStatusClass = (v: unknown) => {
    if (v === "OK") return styles.ok;
    if (v === "FAIL") return styles.fail;
    if (v === "WARN") return styles.warn;
    return "";
  };

  return (
    <div className={styles.wrapper}>
      <table className="data-table">
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c}>{c.replace(/_/g, " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>
                  {c === "status" ? (
                    <span className={`badge ${getStatusClass(row[c])}`}>
                      {String(row[c])}
                    </span>
                  ) : (
                    formatVal(row[c])
                  )}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
