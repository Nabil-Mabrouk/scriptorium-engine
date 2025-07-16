# Frontend Setup Tutorial: Vue 3, Vite, Tailwind CSS, TypeScript

This tutorial guides you through setting up a robust, scalable, and visually appealing frontend for your Scriptorium-Engine (or any similar API-driven project). We'll cover essential tools, configuration, and best practices, specifically addressing common issues like Node.js versioning, Tailwind CSS integration, and path aliases.

**Target Stack:**
*   **Framework:** Vue.js 3 (`<script setup>` syntax)
*   **Build Tool:** Vite
*   **Styling:** Tailwind CSS (utility-first)
*   **Language:** TypeScript
*   **Routing:** Vue Router
*   **State Management:** Pinia
*   **HTTP Client:** Axios
*   **Color Palette:** Turquoise and Black

---

## 0. Prerequisites & Essential Tools

Before you begin, ensure you have the following installed:

*   **Node.js:** Essential for `npm` (Node Package Manager).
    *   **CRITICAL TIP: Use NVM (Node Version Manager)!** Node.js projects often require specific versions. NVM allows you to install and switch between multiple Node.js versions easily. This prevents "Unsupported engine" errors (`EBADENGINE`).
        *   **For Windows:** Use `nvm-windows` (GitHub: `coreybutler/nvm-windows`). Uninstall any existing Node.js first, then install `nvm-windows`.
        *   **For macOS/Linux:** Use `nvm` (GitHub: `nvm-sh/nvm`).
    *   **After installing NVM, install and use a compatible Node.js version.** For current Vue 3/Vite/Tailwind, Node.js `^20.19.0` or `^22.0.0` LTS are usually safe bets.
        ```bash
        nvm install 20  # or nvm install 22
        nvm use 20      # or nvm use 22
        node -v         # Verify it's the correct version
        npm -v          # Verify npm is installed with Node
        ```
*   **npm:** Comes with Node.js.
*   **Code Editor:** Visual Studio Code (highly recommended for its Vue/TypeScript integration).
*   **Git Bash / PowerShell (Windows):** For command-line operations.

---

## 1. Backend CORS Configuration (FastAPI)

Your frontend will run on a different port (e.g., `localhost:5173`) than your FastAPI backend (e.g., `localhost:8000`). Without CORS (Cross-Origin Resource Sharing) configuration, your browser will block API requests from the frontend.

**Action:** Open `C:\Projects\57-scriptorium-engine\src\main.py` and add the `CORSMiddleware`.

```python
# src/main.py
from fastapi import FastAPI
from src.core.config import settings
from src.core.database import Base, engine
from src.core.task_queue import task_queue
from src.project.chapter_router import router as chapter_router
from src.project.router import router as project_router
from src.project.part_router import router as part_router
from src.crew.router import router as crew_router
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis

# NEW: Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Scriptorium-Engine", version=settings.APP_VERSION)

# NEW: CORS Configuration - Place this BEFORE any router includes
origins = [
    "http://localhost:5173",  # This is the default port for Vite dev server
    # IMPORTANT: Add your production frontend URL(s) here later!
    # e.g., "https://your.production.domain"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

# ... (rest of your existing FastAPI main.py content) ...

# Ensure FastAPI server is restarted after this change:
# uvicorn src.main:app --reload
```

---

## 2. Frontend Project Setup (Vue 3 with Vite & TypeScript)

We'll use Vite to quickly scaffold a new Vue 3 project with TypeScript.

**Action:** Open a **new terminal window**. Navigate to the parent directory where you want to create your frontend project (e.g., `C:\Projects`).

1.  **Create Vue.js Project with Vite:**
    ```bash
    npm create vite@latest scriptorium-frontend -- --template vue-ts
    ```
    *   `scriptorium-frontend` is your project name.
    *   `--template vue-ts` ensures it's a Vue 3 project with TypeScript.

2.  **Navigate into the new project directory:**
    ```bash
    cd scriptorium-frontend
    ```

3.  **Install base project dependencies:**
    ```bash
    npm install
    ```

---

## 3. Install Core Frontend Libraries

Add essential libraries for routing, state management, and API calls.

**Action:** In your `scriptorium-frontend` terminal.

```bash
npm install axios vue-router pinia
```

---

## 4. Configure Tailwind CSS

This is often the trickiest part. We'll set up Tailwind CSS, including its PostCSS integration and the new Vite plugin, along with your custom color palette.

**Action:** In your `scriptorium-frontend` terminal.

1.  **Install Tailwind CSS and its dependencies:**
    ```bash
    npm install -D tailwindcss@latest autoprefixer@latest postcss@latest @tailwindcss/postcss@latest @tailwindcss/vite@latest
    ```
    *   **Note:** We include `@tailwindcss/postcss` and `@tailwindcss/vite` explicitly as these are crucial for the latest Tailwind versions with Vite.

2.  **Initialize Tailwind CSS configuration files:**
    ```bash
    npx tailwindcss init -p
    ```
    *   This creates `tailwind.config.js` and `postcss.config.js`.

3.  **Configure `tailwind.config.js`:**
    *   **Action:** Open `scriptorium-frontend/tailwind.config.js`.
    *   **Ensure `content` paths are correct.** This tells Tailwind which files to scan for classes.
    *   **Add your custom color palette** (`turquoise` and `black`).

    ```javascript
    // scriptorium-frontend/tailwind.config.js
    /** @type {import('tailwindcss').Config} */
    export default {
      content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}", // CRITICAL: Scans all Vue, JS, TS, JSX files in src/
      ],
      theme: {
        extend: {
          colors: {
            // Define your custom colors here
            turquoise: {
              DEFAULT: '#40E0D0', // Primary turquoise
              light: '#6AF2E0',   // Lighter shade for highlights/hovers
              dark: '#35BFB2',    // Darker shade for accents
            },
            black: {
              DEFAULT: '#0A0A0A', // Deep black for backgrounds
              light: '#1A1A1A',   // Slightly lighter black for cards/elements
            },
            // You might want a complementary text color
            white: '#FFFFFF',
            gray: {
              light: '#CCCCCC',
              DEFAULT: '#888888',
              dark: '#444444',
            },
          },
          fontFamily: {
            // Optional: add custom fonts if you desire (e.g., 'Inter' via Google Fonts)
            sans: ['Inter', 'sans-serif'],
          },
        },
      },
      plugins: [],
    }
    ```

4.  **Configure `postcss.config.js`:**
    *   **Action:** Open `scriptorium-frontend/postcss.config.js`.
    *   **CRITICAL:** This configuration uses the specific `@tailwindcss/postcss` plugin for PostCSS compatibility.

    ```javascript
    // scriptorium-frontend/postcss.config.js
    export default {
      plugins: {
        '@tailwindcss/postcss': {}, // CRITICAL: Use the dedicated PostCSS plugin for Tailwind
        autoprefixer: {},
      },
    }
    ```

5.  **Configure `vite.config.ts` for Tailwind Integration & Aliases:**
    *   **Action:** Open `scriptorium-frontend/vite.config.ts`.
    *   **Add the `@tailwindcss/vite` plugin.**
    *   **Define the `@` alias** for `src/` directory.

    ```typescript
    // scriptorium-frontend/vite.config.ts
    import { fileURLToPath, URL } from 'node:url'

    import { defineConfig } from 'vite'
    import vue from '@vitejs/plugin-vue'
    import tailwindcss from '@tailwindcss/vite' // NEW: TailwindCSS Vite plugin

    // https://vitejs.dev/config/
    export default defineConfig({
      plugins: [
        vue(),
        tailwindcss(), // NEW: Add the TailwindCSS Vite plugin
      ],
      resolve: {
        alias: {
          // CRITICAL: Define @ alias pointing to your src directory
          '@': fileURLToPath(new URL('./src', import.meta.url))
        }
      }
    })
    ```

6.  **Import Tailwind CSS into your main CSS file:**
    *   **Action:** Open `scriptorium-frontend/src/assets/main.css`.
    *   **Add the Tailwind directives** and global base styles.

    ```css
    /* scriptorium-frontend/src/assets/main.css */
    @tailwind base;
    @tailwind components;
    @tailwind utilities;

    /* Global styles for the dark theme */
    body {
      @apply bg-black text-white; /* Uses your custom 'black' (which maps to DEFAULT) and 'white' */
      font-family: 'Inter', sans-serif; /* Example font */
    }

    /* Optional: scrollbar styling for dark theme */
    ::-webkit-scrollbar {
      width: 8px;
    }

    ::-webkit-scrollbar-track {
      background: #1a1a1a; /* bg-black-light */
    }

    ::-webkit-scrollbar-thumb {
      background: #40E0D0; /* bg-turquoise-DEFAULT */
      border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
      background: #35BFB2; /* bg-turquoise-dark */
    }
    ```

---

## 5. Configure Vue Router & Pinia

Integrate the routing and state management libraries into your Vue application.

**Action:**

1.  **Create `src/router/index.ts`:**
    *   Create a new folder `router` inside `src`.
    *   Create `index.ts` inside `src/router`.
    *   **CRITICAL:** Use the `@` alias for imports.

    ```typescript
    // scriptorium-frontend/src/router/index.ts
    import { createRouter, createWebHistory } from 'vue-router'
    // CRITICAL: Use the @ alias
    import ProjectListView from '@/views/ProjectListView.vue' // We'll create this view soon

    const router = createRouter({
      history: createWebHistory(import.meta.env.BASE_URL),
      routes: [
        {
          path: '/',
          name: 'projectList',
          component: ProjectListView
        },
        // More routes will go here (e.g., project detail)
      ]
    })

    export default router
    ```

2.  **Modify `src/main.ts` (Vue App Initialization):**
    *   This file bootstraps your Vue application, integrating CSS, Pinia, and Vue Router.

    ```typescript
    // scriptorium-frontend/src/main.ts
    import './assets/main.css' // Import your global CSS (including Tailwind)

    import { createApp } from 'vue'
    import { createPinia } from 'pinia' // For state management

    import App from './App.vue'
    import router from './router' // For routing

    const app = createApp(App)

    app.use(createPinia()) // Use Pinia
    app.use(router) // Use Vue Router

    app.mount('#app')
    ```

---

## 6. Initial Vue Components (App.vue, ProjectListView.vue)

Set up your basic application structure and first view.

**Action:**

1.  **Modify `src/App.vue` (Main Vue Component):**
    *   This is the root component where `RouterView` renders your routes.

    ```vue
    <!-- scriptorium-frontend/src/App.vue -->
    <script setup lang="ts">
    import { RouterView } from 'vue-router'
    </script>

    <template>
      <div class="min-h-screen flex flex-col">
        <!-- Main header -->
        <header class="bg-black-light text-white p-4 shadow-lg">
          <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-bold text-turquoise-light">Scriptorium Engine</h1>
            <!-- Navigation links can go here -->
          </div>
        </header>

        <!-- Main content area where routes are rendered -->
        <main class="flex-grow container mx-auto p-6">
          <RouterView />
        </main>

        <!-- Footer -->
        <footer class="bg-black-light text-gray-light p-4 text-center text-sm">
          &copy; {{ new Date().getFullYear() }} Scriptorium Engine. All rights reserved.
        </footer>
      </div>
    </template>

    <style scoped>
    /* No scoped styles needed if relying heavily on Tailwind */
    </style>
    ```

2.  **Create `src/views/ProjectListView.vue`:**
    *   **CRITICAL:** If the `src/views` folder doesn't exist, create it first: `mkdir src/views` (from `scriptorium-frontend` directory).
    *   Then, create the file `ProjectListView.vue` inside `src/views`.

    ```vue
    <!-- scriptorium-frontend/src/views/ProjectListView.vue -->
    <script setup lang="ts">
    // This will eventually fetch and display projects
    </script>

    <template>
      <div class="p-4 bg-black-light rounded-lg shadow-xl">
        <h2 class="text-3xl font-semibold mb-6 text-turquoise-DEFAULT">Your Projects</h2>
        <p class="text-gray-light">Project list will appear here.</p>
        <button class="mt-4 px-6 py-3 bg-turquoise-DEFAULT text-black rounded-lg font-bold
                       hover:bg-turquoise-light transition duration-300 ease-in-out shadow-md">
          Create New Book Project
        </button>
      </div>
    </template>

    <style scoped>
    /* Specific styles for this view if needed, but Tailwind should cover most */
    </style>
    ```

---

## 7. TypeScript Path Mapping (`tsconfig.json`)

While Vite handles the `@` alias during development and build, TypeScript itself needs to know about it for correct type checking and IDE IntelliSense.

**Action:** Open `scriptorium-frontend/tsconfig.json`.

```json
// scriptorium-frontend/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    // NEW: Add this paths configuration for TypeScript
    "paths": {
      "@/*": ["./src/*"] // This maps @/anything to ./src/anything
    }
  },
  "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## 8. Final Cleanup & First Run

Before the first run, perform a thorough cleanup to avoid any lingering cache issues from previous attempts or partial installations.

**Action:** In your `scriptorium-frontend` terminal.

1.  **Completely stop your Vite dev server** (Ctrl+C if it was running).

2.  **Aggressively clean Node.js modules and caches:**
    ```bash
    # In scriptorium-frontend directory
    rm -rf node_modules # Delete the node_modules folder
    rm package-lock.json # Delete the package-lock.json file
    rm -rf .vite # Delete Vite's cache folder (if it exists)
    npm cache clean --force # Clear npm's cache (confirms Node.js is the source of truth)
    ```
    *   *(For PowerShell users, `Remove-Item -Recurse -Force node_modules` and `Remove-Item package-lock.json`)*

3.  **Reinstall all dependencies cleanly:**
    ```bash
    npm install
    ```
    *   **CRITICAL CHECK DURING THIS STEP:** Observe the output for any `npm warn EBADENGINE Unsupported engine` messages. If you see them, **stop** and revisit Node.js version management (Section 0) until `node -v` shows a compatible version and `npm install` runs without this specific warning.

4.  **Start the Vite development server:**
    ```bash
    npm run dev
    ```

5.  **Open your web browser** and go to the URL provided by Vite (usually `http://localhost:5173`).

You should now see your basic "Your Projects" page with the turquoise and black theme, free of compilation errors!

---

## 9. IDE Setup (VS Code Volar)

For the best developer experience in VS Code, install the official Vue Language Features extension.

**Action:**

1.  **Open VS Code.**
2.  Go to the **Extensions view** (`Ctrl+Shift+X`).
3.  Search for `Volar`.
4.  Install **"Vue Language Features (Volar)"** by `Vue.js`.
5.  *(Optional but recommended if you had Vue 2 projects):* If you had the old **Vetur** extension, disable it to prevent conflicts with Volar.
6.  Reload VS Code (`Ctrl+Shift+P` -> "Reload Window").

Your Vue `.vue` files will now have proper syntax highlighting, IntelliSense, and error checking for Vue 3, TypeScript, and Tailwind CSS.

---

## Troubleshooting Guide (Based on Our Experience)

Here's a quick reference for the specific errors we encountered and their solutions:

*   **Error:** `ModuleNotFoundError: No module named 'fastapi_limiter'`
    *   **Cause:** The `fastapi-limiter` Python package was not installed in your backend's virtual environment.
    *   **Fix:** `pip install fastapi-limiter[redis]` in your backend's virtual environment.

*   **Error:** `NameError: name 'ChatOpenAI' is not defined` (or similar for LangChain imports in `crew/agents.py`)
    *   **Cause:** Remnants of old LangChain `ChatOpenAI` setup were left after migrating to `openai-agents`.
    *   **Fix:** Delete the `llm = ChatOpenAI(...)` initialization block from `src/crew/agents.py`. Ensure all LangChain imports are removed if not used.

*   **Error:** `AttributeError: 'RunResult' object has no attribute 'usage'`
    *   **Cause:** Incorrectly trying to access `run_result.usage` when the `usage` attribute is nested within `run_result.raw_responses[0].usage`.
    *   **Fix:** In `src/crew/service.py`, update `log_crew_run` to correctly parse `usage_metrics.raw_responses[0].usage`. Also, ensure `run_*_crew` methods pass `usage_metrics=run_result` (the whole `RunResult` object) to `log_crew_run`.

*   **Error:** `AttributeError: 'PartListOutline' object has no attribute 'chapters'` (during `run_chapter_detailing_crew`)
    *   **Cause:** The `architect_part_agent` (configured to output `PartListOutline`) was incorrectly used for chapter detailing, which expects `ChapterListOutline`.
    *   **Fix:** Create a new `architect_chapter_agent` in `src/crew/agents.py` with `output_type=ChapterListOutline` and update `run_chapter_detailing_crew` in `src/crew/service.py` to use this new agent.

*   **Error:** `sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called; can't call await_only() here.` (during `part.chapters.clear()` or `ProjectDetailRead` serialization)
    *   **Cause:** An asynchronous database operation (like clearing a relationship or lazy loading a relationship for serialization) was attempted in a synchronous context.
    *   **Fix (`finalize_chapter_structure`):** Replace `part.chapters.clear()` with a direct `await session.execute(delete(Chapter).where(Chapter.part_id == part.id))` query.
    *   **Fix (Response Model):** For API endpoints returning models with nested relationships (`PartReadWithChapters`, `ProjectDetailRead`), ensure the relationship is *eagerly loaded* in the service function (e.g., `selectinload(Part.chapters)`) before the database session is closed.

*   **Error:** `[vite] Internal server error: Failed to resolve import "../views/ProjectListView.vue" from "src/router/index.ts". Does the file exist?`
    *   **Cause 1:** The file/folder `src/views/ProjectListView.vue` literally did not exist or had incorrect casing.
    *   **Fix 1:** Manually create the `src/views` folder and `ProjectListView.vue` file inside it with the correct content and casing.
    *   **Cause 2:** Vite/TypeScript path alias was not correctly configured or picked up.
    *   **Fix 2:**
        1.  Ensure `vite.config.ts` has the `@` alias defined: `alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }`.
        2.  Ensure `tsconfig.json` has the corresponding `paths` mapping: `"@/*": ["./src/*"]`.
        3.  Ensure the import in `src/router/index.ts` uses the alias: `import ProjectListView from '@/views/ProjectListView.vue'`.
        4.  Perform an aggressive cleanup: `rm -rf node_modules package-lock.json .vite && npm cache clean --force && npm install`.

*   **Error:** `[postcss] It looks like you're trying to use 'tailwindcss' directly as a PostCSS plugin...`
    *   **Cause:** Incorrect or outdated Tailwind CSS PostCSS configuration for Vite.
    *   **Fix:**
        1.  Ensure all correct Tailwind dependencies are installed: `npm install -D tailwindcss@latest autoprefixer@latest postcss@latest @tailwindcss/postcss@latest @tailwindcss/vite@latest`.
        2.  Update `postcss.config.js`: `export default { plugins: { '@tailwindcss/postcss': {}, autoprefixer: {}, }, }`.
        3.  Update `vite.config.ts` plugins: `plugins: [ vue(), tailwindcss(), ]`.
        4.  Perform an aggressive cleanup: `rm -rf node_modules package-lock.json .vite && npm cache clean --force && npm force install`.
        5.  **CRITICAL:** Verify no `npm warn EBADENGINE` Node.js version warnings during `npm install`.

*   **Error:** `Cannot apply unknown utility class 'bg-black-DEFAULT'`
    *   **Cause:** Using `DEFAULT` suffix explicitly for custom colors in Tailwind classes (`bg-black-DEFAULT`) when it should be omitted (`bg-black`).
    *   **Fix:** Change `bg-black-DEFAULT` to `bg-black` (and similar for any other `*-DEFAULT` usage) in your Vue templates and CSS files.

