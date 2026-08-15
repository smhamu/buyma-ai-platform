import type { Paginated } from "../../modules/research-common/types";

export function Pagination({page,onPage,onPageSize}:{page:Paginated<unknown>;onPage:(page:number)=>void;onPageSize:(size:number)=>void}) {
  return <div className="pagination-bar" aria-label="Pagination"><div>Page {page.page} of {Math.max(page.total_pages,1)} · Total {page.total}</div><div className="pagination-actions"><select className="form-field__input pagination-size" aria-label="Page size" value={page.page_size} onChange={e=>onPageSize(Number(e.target.value))}><option>20</option><option>50</option><option>100</option></select><button className="secondary-button" disabled={page.page<=1} onClick={()=>onPage(page.page-1)}>Previous</button><button className="secondary-button" disabled={page.page>=page.total_pages} onClick={()=>onPage(page.page+1)}>Next</button></div></div>;
}
