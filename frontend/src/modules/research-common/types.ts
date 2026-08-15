export type Paginated<T> = { items: T[]; page: number; page_size: number; total: number; total_pages: number };
export type SortOrder = "asc" | "desc";
