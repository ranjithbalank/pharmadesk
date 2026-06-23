import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { FileSpreadsheet, FileText, Download } from 'lucide-react'
import { api, downloadFile } from '../lib/api'
import type { ReportData } from '../lib/types'
import { PageHeader, Empty } from '../components/ui'

const REPORTS = [
  { key: 'stock_valuation', label: 'Stock & Valuation' },
  { key: 'low_stock', label: 'Low / Out-of-Stock' },
  { key: 'near_expiry', label: 'Near-Expiry' },
  { key: 'sales', label: 'Sales', dated: true },
  { key: 'gst_summary', label: 'GST Summary', dated: true },
  { key: 'schedule_h1', label: 'Schedule H1 Register' },
]

export default function Reports() {
  const [active, setActive] = useState(REPORTS[0])
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')

  const params: Record<string, string> = {}
  if (start) params.start = start
  if (end) params.end = end

  const { data, isFetching } = useQuery({
    queryKey: ['report', active.key, start, end],
    queryFn: async () =>
      (await api.get<ReportData>(`/reports/${active.key}/`, { params })).data,
  })

  const exportUrl = (fmt: string) => {
    const qs = new URLSearchParams({ ...params, export: fmt }).toString()
    downloadFile(`/reports/${active.key}/?${qs}`, `${active.label.replace(/ /g, '_')}.${fmt}`)
  }

  return (
    <div>
      <PageHeader title="Reports" subtitle="Run against local data — works fully offline" />

      <div className="flex flex-wrap gap-2 mb-4">
        {REPORTS.map((r) => (
          <button key={r.key} onClick={() => setActive(r)}
            className={`px-3.5 py-2 rounded-lg text-[12.5px] font-semibold border transition ${
              active.key === r.key ? 'bg-accent text-white border-accent' : 'bg-white border-line text-muted hover:border-accent/40'
            }`}>
            {r.label}
          </button>
        ))}
      </div>

      <div className="card">
        <div className="flex items-center justify-between px-5 py-3 border-b border-line gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <h3 className="font-bold text-[15px]">{data?.title ?? active.label}</h3>
            {data && <span className="text-[12px] text-muted">{data.count} rows</span>}
          </div>
          <div className="flex items-center gap-2">
            {active.dated && (
              <>
                <input type="date" value={start} onChange={(e) => setStart(e.target.value)}
                  className="border border-line rounded-lg px-2.5 py-1.5 text-[12px]" />
                <span className="text-muted text-[12px]">to</span>
                <input type="date" value={end} onChange={(e) => setEnd(e.target.value)}
                  className="border border-line rounded-lg px-2.5 py-1.5 text-[12px]" />
              </>
            )}
            <button className="btn-ghost !py-1.5" onClick={() => exportUrl('xlsx')}>
              <FileSpreadsheet size={15} /> Excel
            </button>
            <button className="btn-ghost !py-1.5" onClick={() => exportUrl('pdf')}>
              <FileText size={15} /> PDF
            </button>
          </div>
        </div>

        <div className="overflow-x-auto max-h-[60vh]">
          {isFetching && <Empty>Loading…</Empty>}
          {data && data.rows.length === 0 && <Empty>No data for this report.</Empty>}
          {data && data.rows.length > 0 && (
            <table className="w-full text-[12.5px]">
              <thead className="bg-canvas text-muted text-[11px] uppercase tracking-wide sticky top-0">
                <tr>
                  {data.columns.map((c) => <th key={c} className="text-left font-semibold px-4 py-2.5 whitespace-nowrap">{c}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {data.rows.map((row, i) => (
                  <tr key={i} className="hover:bg-canvas/60">
                    {row.map((cell, j) => (
                      <td key={j} className={`px-4 py-2 whitespace-nowrap ${typeof cell === 'number' ? 'text-right font-mono' : ''}`}>
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
              {data.total != null && (
                <tfoot>
                  <tr className="bg-canvas font-bold">
                    <td className="px-4 py-2.5" colSpan={data.columns.length - 1}>Total</td>
                    <td className="px-4 py-2.5 text-right font-mono">{data.total.toLocaleString('en-IN')}</td>
                  </tr>
                </tfoot>
              )}
            </table>
          )}
        </div>
      </div>

      <p className="text-[12px] text-muted mt-3 flex items-center gap-1.5">
        <Download size={13} /> Every report exports to Excel (.xlsx) and PDF.
      </p>
    </div>
  )
}
