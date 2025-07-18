## Part 1: Frontend General Specification (The "Why" and "How" for any Frontend)

This specification outlines the architectural philosophy, standard practices, and core structure for all your Vue.js frontend applications. It ensures they are aligned with the principles established for the backend.

### 1. Frontend Project Goal

To establish a standardized, highly reusable, performant, and user-friendly frontend architecture for AI-powered automation applications, built on modern Vue.js and TypeScript. This specification aims to accelerate UI development, ensure consistency, and provide a robust foundation for rich user experiences.

### 2. Core Architectural Principles

*   **Modularity & Component-Based Design:**
    *   **Why:** Break down complex UIs into smaller, independent, reusable components. This improves maintainability, testability, and promotes a consistent look and feel.
    *   **Implementation:** Clear separation into `base` (UI primitives) and `features` (domain-specific composites) components.
*   **Reactive State Management:**
    *   **Why:** Centralize application data and logic that needs to be shared across multiple components or persists across route changes. Provides a single source of truth and predictable state changes.
    *   **Implementation:** Pinia for global state management.
*   **Strict Type Safety:**
    *   **Why:** Prevent common runtime errors, improve code readability, and enable powerful IDE tooling (autocompletion, refactoring). Crucial for aligning with the backend's Pydantic schemas.
    *   **Implementation:** TypeScript with types derived directly from the backend's OpenAPI specification (`openapi-typescript`).
*   **Robust API Interaction & Asynchronous Workflow Handling:**
    *   **Why:** Frontend applications must reliably communicate with the backend, handle loading states, and provide feedback for long-running background tasks.
    *   **Implementation:** Axios for HTTP requests, Pinia stores for managing loading/error states and orchestrating API calls, dedicated "task" store for polling background job statuses, `processingIds` for granular UI feedback.
*   **User-Centric Design & Feedback:**
    *   **Why:** Provide a smooth, responsive, and informative user experience. Users should always know what the system is doing, whether an operation is in progress, successful, or has failed.
    *   **Implementation:** Loading indicators, disabled states for buttons during processing, non-blocking notification system (toasts), clear error messages.
*   **Performance & Responsiveness:**
    *   **Why:** Ensure the application loads quickly and is usable across various devices and screen sizes.
    *   **Implementation:** Vite for fast dev and optimized builds, Tailwind CSS for efficient styling, responsive design principles.
*   **Testability:**
    *   **Why:** Ensure UI components and logic function as expected, reducing regressions.
    *   **Implementation:** Clear component props/emits, isolated store actions, unit tests for components, stores, and composables.
*   **Reusability:**
    *   **Why:** Reduce boilerplate code and accelerate development of new features or projects.
    *   **Implementation:** Generic `Base` components, reusable Pinia stores (e.g., `task` store), `composables` for shared logic.

### 3. Standardized Technology Stack

*   **Framework:** Vue.js 3 (with Composition API, `<script setup>`)
*   **State Management:** Pinia
*   **Routing:** Vue Router
*   **Build Tool:** Vite
*   **Language:** TypeScript
*   **HTTP Client:** Axios
*   **Styling:** Tailwind CSS
*   **Testing:** Vitest (unit tests), Vue Test Utils (component tests), (Optional: Playwright/Cypress for E2E)
*   **Type Generation:** `openapi-typescript` (run as a build step or manually)

### 4. High-Level Project Structure

```
.
├── src/
│   ├── assets/                # Static assets (images, fonts)
│   │   ├── images/
│   │   └── styles/            # Global CSS, Tailwind base
│   │       ├── base.css
│   │       └── main.css
│   │
│   ├── components/
│   │   ├── base/              # Reusable UI primitives (buttons, inputs, modals)
│   │   │   ├── BaseButton.vue
│   │   │   ├── BaseInput.vue
│   │   │   └── BaseModal.vue
│   │   │   └── ... (other common UI elements)
│   │   │
│   │   ├── features/          # Domain-specific components (e.g., InvoiceCard, ChapterEditor)
│   │   │   ├── <project_domain_1>/ # Encapsulates components unique to a domain
│   │   │   │   └── <DomainComponentA>.vue
│   │   │   │   └── <DomainComponentB>.vue
│   │   │   └── ...
│   │   │
│   │   └── layout/            # Application layout components (sidebar, header, main layout)
│   │       └── AppLayout.vue
│   │       └── ...
│   │
│   ├── composables/           # Reusable Vue logic (e.g., useLocalStorage, useDebounce)
│   │   └── use<Feature>.ts
│   │
│   ├── lib/                   # Utility libraries and auto-generated types
│   │   ├── api.ts             # Centralized Axios instance
│   │   └── types.ts           # Auto-generated from backend OpenAPI (via openapi-typescript) - ONLY SOURCE OF TRUTH
│   │
│   ├── pages/                 # Top-level route components (Dashboard, DetailPage)
│   │   └── Dashboard.vue
│   │   └── ProjectDetailPage.vue # Example
│   │   └── ...
│   │
│   ├── router/
│   │   └── index.ts           # Vue Router configuration
│   │
│   ├── stores/                # Pinia stores for global state management
│   │   ├── <project_domain_1>.ts # Domain-specific store (e.g., project.ts, invoice.ts)
│   │   ├── task.ts            # Generic store for background job polling
│   │   └── ui.ts              # Generic store for UI state (e.g., notifications, modal visibility)
│   │
│   ├── views/                 # (Optional: can be merged with pages if not distinguishing)
│   │   └── HomeView.vue
│   │   └── AboutView.vue
│   │
│   ├── App.vue                # Main Vue application component
│   └── main.ts                # Application entry point
├── public/                    # Static files served directly (e.g., index.html, favicon)
├── index.html                 # Main HTML file
├── vite.config.ts             # Vite build configuration
├── tsconfig.json              # TypeScript configuration
└── package.json               # Node.js project metadata and scripts
```

### 5. Standardized Workflow for API Interaction & Task Polling

This aligns directly with the backend's asynchronous processing model:

1.  **User Interaction:** A user clicks a button or performs an action in a `components/features` component or `pages` component.
2.  **Dispatch Action:** The component dispatches an action to the relevant **Pinia store** (e.g., `projectStore.generateParts()`).
3.  **Initiate API Call:** The Pinia store action makes an asynchronous API call using `src/lib/api.ts` (e.g., `apiClient.post('/crew/generate-parts/...')`).
    *   **Immediate Feedback:** The store updates a `processingIds` Set or `isLoading` flag *immediately* to disable/show loading states in the UI.
4.  **Backend Response (202 Accepted):** The backend responds with `HTTP 202 Accepted` and a `job_id` (using `TaskStatus` schema).
5.  **Task Store Orchestration:** The calling store (e.g., `projectStore`) dispatches the `job_id` and relevant context (`projectId`, `partId`, `chapterId` or `entityIdToUpdateStatusFor`) to the **`src/stores/task.ts`** store.
6.  **Polling Loop:** The `task.ts` store initiates a polling interval (e.g., every 3 seconds) by repeatedly calling the backend's `GET /crew/status/{job_id}` endpoint.
7.  **Status Update & UI Refresh:**
    *   If `status === 'complete'` or `status === 'success'`:
        *   `task.ts` clears its interval.
        *   `task.ts` notifies the original store (e.g., by calling `projectStore.fetchProjectById()` or a dedicated `onTaskComplete` method).
        *   `task.ts` removes the `entityIdToUpdateStatusFor` from the `processingIds` Set.
        *   The UI automatically updates due to reactivity, showing the new data and enabling buttons.
        *   A success toast notification is displayed (via `ui.ts` store).
    *   If `status === 'failed'` or `status === 'error'`:
        *   `task.ts` clears its interval.
        *   `task.ts` removes the `entityIdToUpdateStatusFor` from `processingIds`.
        *   An error toast notification is displayed (via `ui.ts` store), potentially showing `response.data.error`.
8.  **Human in the Loop:** For steps requiring user validation or editing (e.g., reviewing generated outlines), the UI presents editable forms. On submission, a `PUT` request is made to the backend (e.g., `/projects/{id}/finalize-parts`), and the relevant Pinia store refreshes the data.

### 6. Styling Guidelines

*   **Utility-First CSS:** Use Tailwind CSS classes directly in components for rapid development and consistent styling.
*   **Theming:** Define a consistent color palette, typography, and spacing through Tailwind's configuration.
*   **Responsiveness:** Prioritize mobile-first design, utilizing Tailwind's responsive prefixes (e.g., `md:`, `lg:`).
*   **Minimal Custom CSS:** Avoid writing custom CSS unless absolutely necessary for complex, highly specific styles not achievable with Tailwind. If custom CSS is required, it should reside in the component's `<style>` block (scoped).

### 7. Testing Guidelines

*   **Unit Tests (Vitest & Vue Test Utils):**
    *   **Components:** Test rendering, prop reactivity, event emissions, and basic user interactions in isolation. Mock Pinia stores and API calls.
    *   **Pinia Stores:** Test actions, getters, and state mutations independently.
    *   **Composables:** Test their reactive logic and any side effects.
*   **End-to-End (E2E) Tests (Optional: Playwright/Cypress):**
    *   Automate user flows through the entire application, interacting with the real backend (or a mocked one for CI/CD).

### 8. Developer Experience

*   **Linting & Formatting:** Enforce consistent code style using ESLint and Prettier.
*   **Type Checking:** Ensure TypeScript compiler (`tsc`) runs without errors.
*   **Vue DevTools:** Encourage use for debugging state and component hierarchy.
*   **Clear `package.json` Scripts:** Define scripts for dev server, build, lint, test, and type generation.

---

