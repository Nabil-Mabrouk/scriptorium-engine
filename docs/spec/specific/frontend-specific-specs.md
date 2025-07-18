## Part 2: Frontend Project-Specific Specification Template

This template captures the unique UI requirements, data flows, and interactions for a *specific* new project. It directly aligns with the Backend Project-Specific Specification.

---

### Project-Specific Frontend Specification: `[<Your Project Name>]`

---

#### 1. Project Overview & UI Goal

*   **Project Name:** `[e.g., Invoice Processor Frontend, Recipe Generator UI]` (Must match backend project name)
*   **Frontend Brief Description:** `[A concise summary of the frontend's primary role and user experience. E.g., "A web interface for users to upload invoices, monitor their processing status, review extracted data, and manage categorized invoices."]`
*   **Key User Interface Goal:** `[What is the overarching UX objective? E.g., "To provide an intuitive, step-by-step experience for invoice automation, minimizing human intervention where possible and clearly highlighting areas for review."] `

---

#### 2. Key Pages/Views & Their Purpose (`src/pages/`)

Define the main application screens.

*   **Project Domain Folder Name:** `[e.g., 'invoice', 'recipe', 'chatbot']` (Must match the backend's `src/<project_domain_name>/` folder name)
*   **Page 1: `<Page Name>`** (e.g., `Invoice Dashboard`, `Recipe Library`)
    *   **Path:** `[e.g., '/', '/invoices']`
    *   **Component Name:** `[e.g., 'InvoiceDashboard.vue']`
    *   **Purpose:** `[What is displayed on this page? What is its main function? E.g., "Displays a list of all invoices with their current status and total cost."] `
    *   **Key Data Displayed:** `[List entities/properties shown, e.g., "Invoice ID, Status, Total Amount, Vendor, Creation Date."] `
    *   **Main User Interactions:** `[List actions, e.g., "Create new invoice (via modal), View invoice details, Filter invoices."] `
    *   **Associated Backend Endpoints (GETs):** `[e.g., "GET /invoices", "GET /users"]`
*   **Page 2: `<Page Name>`** (e.g., `Invoice Detail Page`, `Recipe Creation Page`)
    *   **Path:** `[e.g., '/invoices/:id']`
    *   **Component Name:** `[e.g., 'InvoiceDetailPage.vue']`
    *   **Purpose:** `[Displays detailed information for a single entity, and allows initiation of workflows or editing. E.g., "Shows all extracted invoice data, processing history, and provides controls for data correction and workflow progression."] `
    *   **Key Data Displayed:** `[e.g., "Invoice document preview, Extracted fields (structured JSON), Line items, Processing logs, Version history (if applicable)."] `
    *   **Main User Interactions:** `[e.g., "Trigger OCR, Trigger validation, Edit extracted data, Mark as reviewed."] `
    *   **Associated Backend Endpoints (GETs):** `[e.g., "GET /invoices/{id}", "GET /invoices/{id}/versions"]`
*   **Modal/Dialog 1: `<Modal Name>`** (e.g., `CreateInvoiceModal`)
    *   **Purpose:** `[e.g., "Allows users to upload a new invoice document or paste raw text to create an initial invoice record."] `
    *   **Component Name:** `[e.g., 'components/features/<project_domain_name>/CreateInvoiceModal.vue']` (Will utilize `BaseModal.vue`)
    *   **Input Fields:** `[e.g., "File upload input", "Textarea for raw invoice text"]`
    *   **Action:** `[e.g., "Calls projectStore.createInvoice"]`

---

#### 3. Core Workflows (User Journeys) & Associated UI (`src/stores/`, `src/components/features/`)

Detail how the frontend implements the backend's processing phases and how the UI reacts. **Align `Workflow Name` and `Phase Name` directly with the backend specification.**

*   **Workflow: `<Workflow Name>`** (e.g., `Invoice Processing Workflow`)
    *   **Matches Backend Workflow:** `[Specify the exact backend workflow name this corresponds to]`
    *   **Phase 1: `<Phase Name>`** (e.g., `Document OCR`)
        *   **Corresponding Backend Phase:** `[Specify the exact backend phase name]`
        *   **Triggering UI:** `[e.g., "Button: 'Process Invoice' on InvoiceDetailPage"]`
        *   **Associated Store Action:** `[e.g., "invoiceStore.processInvoice(invoiceId)"]`
        *   **UI State During Processing:** `[e.g., "Triggering button becomes disabled and shows 'Processing...', a spinner appears on the invoice card."] ` (Leverages `invoiceStore.processingIds`)
        *   **Backend Orchestration Endpoint:** `[e.g., "POST /orchestrate/process-document/{invoice_id}"]`
        *   **Data Displayed/Edited After Phase:** `[e.g., "InvoiceDetail page reloads, new 'extracted_data' fields appear, Invoice Status updates to 'OCR_COMPLETED'."]`
        *   **Expected UI After Completion:** `[e.g., "Button changes to 'Review Data', extracted fields are displayed for editing."]`
    *   **Phase 2: `<Phase Name>`** (e.g., `Data Validation & Categorization`)
        *   **Corresponding Backend Phase:** `[Specify the exact backend phase name]`
        *   **Triggering UI:** `[e.g., "Section: 'Data Review', Component: 'InvoiceDataTable.vue']`
        *   **Associated Store Action:** `[e.g., "invoiceStore.validateInvoiceData(invoiceId, validatedData)"]`
        *   **UI for Human Review/Editing:** `[Describe editable components. E.g., "Editable table for line items, dropdowns for categorization, text inputs for vendor/date."] `
        *   **Validation Rules (Frontend):** `[List any frontend-specific input validation (e.g., "Amount must be numeric").]`
        *   **Backend Finalization Endpoint:** `[e.g., "PUT /invoices/{invoice_id}/finalize-data"]`
        *   **Expected UI After Completion:** `[e.g., "Invoice status changes to 'VALIDATED', table becomes read-only, next action (e.g., 'Export') becomes available."] `
    *   ... (repeat structure for all core workflows and phases)

---

#### 4. Component Library Utilization (`src/components/base/`, `src/components/features/`)

*   **Reusable Base Components (`src/components/base/`):**
    *   List all standard `Base` components that will be used.
    *   `BaseButton.vue`: `[e.g., primary, secondary, danger variants, sm/md/lg sizes]`
    *   `BaseInput.vue`: `[e.g., text, number, textarea types, various states]`
    *   `BaseModal.vue`: `[e.g., visibility control, slots for header/body/footer]`
    *   `BaseSpinner.vue`: `[e.g., simple loading spinner component]`
    *   `BaseNotification.vue` / `useToast.ts`: `[e.g., toast/snackbar notification system]`
    *   `BaseDropdown.vue`: `[If any select/dropdowns are needed]`
*   **New Domain-Specific Feature Components (`src/components/features/<project_domain_name>/`):**
    *   `[e.g., InvoiceCard.vue]`: `[Displays summary of an invoice, routes to detail page.]`
    *   `[e.g., InvoiceDataTable.vue]`: `[Displays and allows editing of extracted invoice line items.]`
    *   `[e.g., ProcessingHistory.vue]`: `[Displays a timeline of processing events for an entity.]`

---

#### 5. Data Modeling & State Management (`src/lib/types.ts`, `src/stores/`)

*   **TypeScript Types Source:** **ALL frontend data types (`interface` or `type`) MUST be imported from `src/lib/types.ts`**, which is auto-generated by `openapi-typescript` from the backend's OpenAPI schema. **No manual re-definition of backend entity types.**
*   **Pinia Stores:**
    *   **`src/stores/<project_domain_name>.ts`**: (e.g., `invoice.ts`, `recipe.ts`)
        *   **Purpose:** Manages the state of `<project_domain_name>` entities (e.g., `invoices`, `recipes`).
        *   **Key State:** `[e.g., 'invoices: InvoiceRead[]', 'activeInvoice: InvoiceDetailRead | null', 'isLoading: boolean', 'error: string | null']`
        *   **Actions:** `[e.g., 'fetchInvoices()', 'fetchInvoiceById(id)', 'createInvoice(payload)', 'finalizeInvoice(id, data)', 'processInvoice(id)']`
        *   **Getters:** `[e.g., 'totalUnprocessedInvoices']`
    *   **`src/stores/task.ts`**:
        *   **Purpose:** Generic store for managing and polling the status of long-running background jobs.
        *   **Key State:** `activePolls: Map<string, number>` (Maps `job_id` to `intervalId`), `processingIds: Set<string>` (Maps `entity_id` to track UI processing states).
        *   **Actions:** `pollJobStatus(jobId: string, entityIdToUpdateStatusFor: string, projectIdToRefresh: string)` (or general `mainEntityIdToRefresh`), `cancelPoll(jobId)`.
    *   **`src/stores/ui.ts`**: (Recommended new general store)
        *   **Purpose:** Manages global UI state (e.g., notifications, global loading, modal visibility for `BaseModal`).
        *   **Key State:** `notifications: Notification[]`, `isGlobalLoading: boolean`.
        *   **Actions:** `showSuccessToast(message)`, `showErrorToast(message)`, `showInfoToast(message)`.

---

#### 6. API Integration Details (`src/lib/api.ts`)

*   **API Client:** `src/lib/api.ts` provides the `apiClient` Axios instance.
*   **Request/Response Types:** All requests and responses will be typed using the interfaces imported from `src/lib/types.ts`.
*   **Example API Calls:**
    *   `projectStore.createProject(blueprint)` -> `apiClient.post<ProjectRead>('/projects', { raw_blueprint: blueprint })`
    *   `projectStore.generateParts(projectId)` -> `apiClient.post<TaskStatus>(`/crew/generate-parts/${projectId}`)`
    *   `taskStore.pollJobStatus(jobId, ...)` -> `apiClient.get<TaskStatus>(`/crew/status/${jobId}`)`

---

#### 7. User Feedback & Error Handling

*   **Loading States:**
    *   Global: `uiStore.isGlobalLoading` for full-screen loaders (rare).
    *   Per-Operation: `projectStore.isLoading` (for page/list fetch), `projectStore.processingIds` (for individual entity operations).
    *   UI elements (buttons, sections) should use these states to disable or show spinners.
*   **Notifications:** Implement a non-blocking toast/snackbar system controlled by `uiStore.showSuccessToast`, `uiStore.showErrorToast`.
*   **Error Display:** `projectStore.error` for page-level errors. For API call errors, they should be caught in the Pinia store action, logged to console, converted to user-friendly messages, and dispatched to the `uiStore` for a toast.

---

#### 8. Design & Styling Notes

*   **Primary Palette:** `[e.g., Teal-600 (primary), Slate-800 (background), Slate-200 (text)]`
*   **Typography:** `[e.g., 'Inter' font, default sizes]`
*   **Spacings:** `[e.g., Tailwind default spacing scale]`
*   **Responsive Breakpoints:** `[e.g., md:, lg:, xl: from Tailwind config]`
*   **Animations/Transitions:** `[e.g., subtle transitions on hover, state changes]`

---