const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Product = {
  id: string;
  name: string;
  product_code?: string | null;
  manufacturer?: string | null;
  category?: string | null;
  description?: string | null;
  quality_score: number;
  status: string;
  created_at: string;
  updated_at: string;
};

export type DashboardSummary = {
  total_products: number;
  products_processed: number;
  average_quality: number;
  validation_issues: number;
  recent_products: {
    id: string;
    name: string;
    category: string | null;
    status: string;
    quality_score: number;
  }[];
};

export type ExtractionResponse = {
  document_id: string;
  filename: string;
  document_type: string;
  extracted_text: string;
  char_count: number;
  page_count: number | null;
  product_id: string | null;
};

export type Specification = {
  id: string;
  product_id: string;
  field_name: string;
  value: string | null;
  normalized_value: string | null;
  unit: string | null;
  confidence: number;
  status: string;
  source: string;
  source_page: number | null;
};

export type ValidationResultItem = {
  id: string;
  field_name: string;
  severity: string;
  message: string | null;
  status: string;
};

export type DocumentItem = {
  id: string;
  filename: string;
  document_type: string | null;
  uploaded_at: string;
};

export type ProductDetail = Product & {
  specifications: Specification[];
  documents: DocumentItem[];
  validation_results: ValidationResultItem[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status} ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  listProducts: () => request<Product[]>("/api/products"),

  getProduct: (id: string) => request<ProductDetail>(`/api/products/${id}`),

  dashboardSummary: () => request<DashboardSummary>("/api/products/dashboard/summary"),

  uploadDocument: (form: FormData) =>
    request<ExtractionResponse>("/api/products/upload", {
      method: "POST",
      body: form,
    }),

  processProduct: (id: string) =>
    request<ProductDetail>(`/api/products/${id}/process`, { method: "POST" }),

  createProduct: (payload: {
    name: string;
    product_code?: string;
    manufacturer?: string;
    category?: string;
    description?: string;
  }) =>
    request<Product>("/api/products", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export { API_URL };
