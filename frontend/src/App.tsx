import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "./components/layout/AppLayout";
import { ProtectedRoute } from "./components/routing/ProtectedRoute";
import { PublicOnlyRoute } from "./components/routing/PublicOnlyRoute";
import { DocumentDetailPage } from "./pages/DocumentDetailPage";
import { KnowledgeBaseDetailPage } from "./pages/KnowledgeBaseDetailPage";
import { KnowledgeBaseDocumentsPage } from "./pages/KnowledgeBaseDocumentsPage";
import { KnowledgeBaseListPage } from "./pages/KnowledgeBaseListPage";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { BrandsPage } from "./pages/BrandsPage";
import { SuppliersPage } from "./pages/SuppliersPage";
import { ProductResearchPage } from "./pages/ProductResearchPage";
import { ProductResearchDetailPage } from "./pages/ProductResearchDetailPage";
import { ResearchIngestionPage } from "./pages/ResearchIngestionPage";
import { SupplierPolicyReviewPage } from "./pages/SupplierPolicyReviewPage";
import { NotificationSettingsPage } from "./pages/NotificationSettingsPage";

export function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />

      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/knowledge-bases" replace />} />
        <Route path="knowledge-bases" element={<KnowledgeBaseListPage />} />
        <Route path="brands" element={<BrandsPage />} />
        <Route path="suppliers" element={<SuppliersPage />} />
        <Route path="product-research" element={<ProductResearchPage />} />
        <Route path="product-research/:id" element={<ProductResearchDetailPage />} />
        <Route path="research-ingestion" element={<ResearchIngestionPage />} />
        <Route path="supplier-policy-review" element={<SupplierPolicyReviewPage />} />
        <Route path="notification-settings" element={<NotificationSettingsPage />} />
        <Route
          path="knowledge-bases/:knowledgeBaseId"
          element={<KnowledgeBaseDetailPage />}
        />
        <Route
          path="knowledge-bases/:knowledgeBaseId/documents"
          element={<KnowledgeBaseDocumentsPage />}
        />
        <Route
          path="knowledge-bases/:knowledgeBaseId/documents/:documentId"
          element={<DocumentDetailPage />}
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
