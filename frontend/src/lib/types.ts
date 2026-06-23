export type StockStatus = 'in_stock' | 'low_stock' | 'out_of_stock'

export interface Batch {
  id: number
  medicine: number
  medicine_name?: string
  batch_number: string
  mfg_date: string | null
  expiry_date: string
  quantity: number
  purchase_cost: string
  mrp: string
  is_expired: boolean
  days_to_expiry: number
}

export interface Medicine {
  id: number
  name: string
  generic_name: string
  manufacturer: string
  hsn_code: string
  gst_rate: string
  schedule: 'OTC' | 'H' | 'H1' | 'X'
  schedule_display?: string
  pack_unit: string
  rack_location: string
  barcode: string
  reorder_level: number
  reorder_qty: number
  min_stock: number | null
  max_stock: number | null
  preferred_supplier: number | null
  is_active: boolean
  total_stock: number
  stock_status: StockStatus
  is_scheduled?: boolean
  sell_mrp?: string
  batches?: Batch[]
}

export interface DayClose {
  date: string
  invoice_count: number
  gross_total: number
  by_mode: Record<string, { count: number; total: number }>
  cash_total: number
  returned_count: number
  returned_total: number
  tax_collected: number
}

export interface Prescription {
  medicine: number
  patient_name: string
  prescriber_name: string
  prescriber_reg_no: string
  quantity: number
}

export interface InvoiceLine {
  id: number
  medicine_name: string
  hsn_code: string
  batch_number: string
  expiry_date: string | null
  quantity: number
  mrp: string
  rate: string
  discount: string
  gst_rate: string
  taxable_value: string
  cgst_amount: string
  sgst_amount: string
  line_total: string
}

export interface Invoice {
  id: number
  number: string
  customer: number | null
  customer_name: string
  payment_mode: 'cash' | 'card' | 'upi' | 'credit'
  payment_mode_display: string
  status: string
  subtotal: string
  discount: string
  cgst: string
  sgst: string
  total: string
  lines: InvoiceLine[]
  created_at: string
}

export interface Customer {
  id: number
  name: string
  phone: string
  address: string
  is_regular: boolean
  allow_credit: boolean
  credit_balance: string
  has_drug_license: boolean
  drug_license_no: string
  consent_given: boolean
  invoice_count?: number
}

export interface PaymentTerm {
  id: number
  name: string
  days: number
  is_active: boolean
}

export interface LeadTime {
  id: number
  label: string
  days: number
  is_active: boolean
}

export interface Supplier {
  id: number
  code: string
  name: string
  gstin: string
  contact_person: string
  phone: string
  email: string
  address: string
  has_drug_license: boolean
  drug_license_no: string
  payment_term: number | null
  payment_term_name?: string
  lead_time: number | null
  lead_time_label?: string
  payment_terms: string
  lead_time_days: number
  is_active: boolean
}

export interface StockMovement {
  id: number
  batch: number
  batch_label: string
  reason: string
  reason_display: string
  quantity: number
  note: string
  actor: string
  reversed: boolean
  created_at: string
}

export interface NotificationItem {
  id: number
  kind: 'low_stock' | 'out_of_stock' | 'near_expiry' | 'reorder'
  kind_display: string
  severity: 'info' | 'warning' | 'critical'
  title: string
  message: string
  medicine: number | null
  medicine_name: string
  created_at: string
}

export interface Dashboard {
  today_sales_total: number
  today_invoice_count: number
  month_sales_total: number
  medicine_count: number
  low_stock_count: number
  out_of_stock_count: number
  near_expiry_count: number
  expired_count: number
  alert_count: number
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ReportData {
  title: string
  columns: string[]
  rows: (string | number)[][]
  count: number
  total: number | null
}
