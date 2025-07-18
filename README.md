# Scriptorium-Engine 📚✍️

Scriptorium-Engine is an AI-powered ghostwriting platform designed to autonomously draft books from a simple idea to a complete manuscript. It leverages a crew of specialized AI agents, each with a unique role, to handle different stages of the book-writing process, from structural outlining to content generation and refinement.

## Core Philosophy

The engine is built on two fundamental principles:

  * **Human-in-the-Loop**: We believe that the best creative work comes from human-AI collaboration. The engine generates drafts and suggestions, but requires human validation and refinement at key milestones to ensure quality, coherence, and authorial intent.
  * **Divide and Conquer**: Writing a book is a monumental task. The engine breaks down the process into smaller, manageable phases: structuring parts, detailing chapters, writing content, and final assembly. This ensures a logical and organized workflow.

## Features

  * **Dynamic Agent Crew**: Utilizes a roster of distinct AI agents (Architect, Theorist, Historian, Technologist, Continuity Editor) for specialized tasks.
  * **Multi-Phase Workflow**: A structured, sequential process that guides a project from a raw idea to a finalized book with an introduction and conclusion.
  * **Asynchronous Task Processing**: Employs `arq` background workers to handle long-running AI generation tasks, ensuring the API remains responsive.
  * **Cost Tracking**: Meticulously tracks OpenAI API token usage and associated costs for every generation task, aggregated at the project level.
  * **Content Versioning**: Automatically saves a new version of a chapter's content every time it is modified, creating a complete revision history.
  * **Resilient Architecture**: Implements a circuit breaker for external API calls to gracefully handle service failures and a rate limiter to prevent abuse.

-----

## System Architecture

The following diagram illustrates the complete data and process flow of the Scriptorium-Engine, from initial project creation to the final, complete book.

\<details\>
\<summary\>\<strong\>Click to view Architecture Diagram\</strong\>\</summary\>

```mermaid
graph TD
    subgraph "Phase 0: Project Setup"
        A[Start: User provides a raw blueprint] -->|1. `POST /projects`| B((Project created in DB));
    end
    
    ---

    subgraph "Phase 1: Part Structuring"
        B -->|2. `POST /crew/generate-parts/{id}`| C[AI generates Draft Part Outline];
        C --> D{Human reviews & edits Parts};
        D -->|3. `PUT /projects/{id}/finalize-parts`| E((Part records created in DB));
    end

    ---

    subgraph "Phase 2: Chapter Detailing (Loop for each Part)"
        E -->|4. `POST /crew/generate-chapters/{part_id}`| F[AI generates Draft Chapter Outline];
        F --> G{Human reviews & edits Chapters};
        G -->|5. `PUT /parts/{part_id}/finalize-chapters`| H((Chapter records created in DB));
    end

    ---
    
    subgraph "Phase 3 & 4: Content & Refinement (Loop for each Chapter)"
        H -->|6. `POST /chapters/{id}/generate`| I[AI writes Chapter Content];
        
        I --> J{Human reviews & edits Content};
        J -->|7. `PUT /chapters/{id}/review`| K((Reviewed Content saved in DB));
        
        I -->|8. `POST /chapters/{id}/analyze-transition`| L[AI analyzes narrative flow];
        L --> J;
    end

    ---

    subgraph "Phase 5: Book Finalization"
        K -->|9. `POST /projects/{id}/finalize`| M[AI writes Intro / Conclusion];
        M --> N([🏆 Complete Book]);
    end
```

\</details\>

-----

## Tech Stack

  * **Backend**: FastAPI
  * **ORM**: SQLAlchemy 2.0 (async)
  * **Database**: PostgreSQL
  * **Task Queue**: `arq`
  * **Cache/Broker**: Redis
  * **Data Validation**: Pydantic
  * **LLM Integration**: `openai-agents`
  * **Frontend**: Vuejs, Vite, tailwindcss

-----

## Getting Started

Follow these instructions to set up and run the project locally.

### 1\. Prerequisites

  * Python 3.12+
  * Docker and Docker Compose
  * An OpenAI API Key

### 2\. Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/Nabil-Mabrouk/scriptorium-engine.git
    cd scriptorium-engine
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
   
    ```bash
    pip install -r base/requirements.txt
    ```

4.  **Set up environment variables:**
    Create a file named `.env` in the project root and populate it with the following values.

    **.env.example**

    ```env
    # --- Core Application Settings ---
    # Your local database connection string
    DATABASE_URL="postgresql+asyncpg://scriptorium:password@localhost:5432/scriptorium_db"
    # Your local Redis connection string
    REDIS_URL="redis://localhost:6379"
    APP_VERSION="0.1.0"
    ENVIRONMENT="development"

    # --- LLM Settings ---
    # Your OpenAI API Key
    OPENAI_API_KEY="sk-..."
    # The default model to use for AI agents if not specified otherwise
    DEFAULT_OPENAI_MODEL_NAME="gpt-4o-mini"
    ```

### 3\. Running the Application

1.  **Start the database and Redis:**
    TODO: The easiest way to run the required services is with Docker. Create a `docker-compose.yml` file in the root directory:

    **docker-compose.yml**

    ```yaml
    version: '3.8'

    services:
      postgres:
        image: postgres:15
        container_name: scriptorium_postgres
        environment:
          POSTGRES_USER: scriptorium
          POSTGRES_PASSWORD: password
          POSTGRES_DB: scriptorium_db
        ports:
          - "5432:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data

      redis:
        image: redis:7
        container_name: scriptorium_redis
        ports:
          - "6379:6379"

    volumes:
      postgres_data:
    ```

    Then, start the services:

    ```bash
    docker-compose up -d
    ```

2.  **Run the FastAPI Server:**
    The application automatically creates the database tables on startup.

    ```bash
    uvicorn src.main:app --reload
    ```

    The API will be available at `http://127.0.0.1:8000`. You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

3.  **Run the ARQ Background Worker:**
    Open a new terminal, activate the virtual environment, and start the worker to process background jobs.

    ```bash
    arq src.crew.worker.WorkerSettings
    ```

    The worker will connect to Redis and wait for tasks to be enqueued by the API.

-----

## API Workflow Guide

This guide walks you through the API calls needed to create a book from start to finish.

### Step 1: Create a Project

First, create a new project with your initial book idea.

  * **Endpoint**: `POST /projects/`
  * **Body**: Your raw idea or blueprint for the book.

<!-- end list -->

```bash
curl -X POST "http://127.0.0.1:8000/projects/" \
-H "Content-Type: application/json" \
-d '{
  "raw_blueprint": "A book about the history and future of artificial intelligence, exploring its philosophical implications and its impact on society, using historical analogies to explain complex concepts."
}'
```

> **Response**: You will get back a project object with a unique `id`. Save this `project_id`.

### Step 2: Generate Part Structure

Use the `project_id` to ask the Architect AI to generate a high-level outline.

  * **Endpoint**: `POST /crew/generate-parts/{project_id}`

<!-- end list -->

```bash
curl -X POST "http://127.0.0.1:8000/crew/generate-parts/YOUR_PROJECT_ID"
```

> This queues a background job. The AI will generate a draft structure, which you can see by fetching the project details (`GET /projects/{project_id}`).

### Step 3: Review and Finalize Parts

After reviewing the draft outline, submit the finalized version to create the official `Part` records.

  * **Endpoint**: `PUT /projects/{project_id}/finalize-parts`
  * **Body**: The user-approved list of parts.

<!-- end list -->

```bash
# In a real app, you would fetch the draft, let the user edit it, then submit it back.
curl -X PUT "http://127.0.0.1:8000/projects/YOUR_PROJECT_ID/finalize-parts" \
-H "Content-Type: application/json" \
-d '{
  "parts": [
    {"part_number": 1, "title": "The Dawn of Calculation", "summary": "From the abacus to early mechanical calculators, exploring the human drive to automate thought."},
    {"part_number": 2, "title": "The Turing Test and the Birth of AI", "summary": "The theoretical foundations of AI and the first attempts at creating thinking machines."},
    {"part_number": 3, "title": "The Age of Neural Networks", "summary": "The rise of deep learning, its triumphs, and its limitations."}
  ]
}'
```

> This creates the `Part` records in the database. Save the `id` for each part.

### Step 4: Generate Chapter Outlines

For each `part_id` from the previous step, generate a detailed chapter outline.

  * **Endpoint**: `POST /crew/generate-chapters/{part_id}`

<!-- end list -->

```bash
curl -X POST "http://127.0.0.1:8000/crew/generate-chapters/YOUR_PART_ID"
```

> Repeat this for every part of your book.

### Step 5: Finalize Chapters

Review the AI-generated chapter drafts for a part and submit the finalized version.

  * **Endpoint**: `PUT /parts/{part_id}/finalize-chapters`
  * **Body**: The user-approved list of chapters for that part.

<!-- end list -->

```bash
# This is an example for a single part.
curl -X PUT "http://127.0.0.1:8000/parts/YOUR_PART_ID/finalize-chapters" \
-H "Content-Type: application/json" \
-d '{
  "chapters": [
    {
      "chapter_number": 1,
      "title": "The Jacquard Loom: Weaving Code",
      "brief": {
        "thesis_statement": "The Jacquard Loom was the first device to use punched cards to control a machine, establishing the fundamental concept of software controlling hardware.",
        "narrative_arc": "Start with the problem of complex textile patterns, introduce Jacquard''s invention, and explain its societal and conceptual impact.",
        "required_inclusions": ["Punched cards", "Automation", "Binary logic"],
        "key_questions_to_answer": ["How did the loom work?", "Why was it revolutionary?"]
      },
      "suggested_agent": "Historian AI"
    }
  ]
}'
```

> This creates the `Chapter` records. Save the `chapter_id` for each.

### Step 6: Generate Chapter Content and Refine

Now, you can generate the content for each chapter and perform quality checks.

1.  **Generate Content**:

      * **Endpoint**: `POST /chapters/{chapter_id}/generate`

    <!-- end list -->

    ```bash
    curl -X POST "http://127.0.0.1:8000/chapters/YOUR_CHAPTER_ID/generate"
    ```

2.  **Analyze Transition** (Optional, for chapters after the first):

      * **Endpoint**: `POST /chapters/{chapter_id}/analyze-transition`

    <!-- end list -->

    ```bash
    curl -X POST "http://127.0.0.1:8000/chapters/YOUR_CHAPTER_ID/analyze-transition"
    ```

3.  **Review and Finalize Content**:

      * **Endpoint**: `PUT /chapters/{chapter_id}/review`

    <!-- end list -->

    ```bash
    curl -X PUT "http://127.0.0.1:8000/chapters/YOUR_CHAPTER_ID/review" \
    -H "Content-Type: application/json" \
    -d '{
      "content": "This is the final, human-edited version of the chapter content...",
      "new_status": "CONTENT_REVIEWED"
    }'
    ```

### Step 7: Finalize the Book

Once all chapters are complete, generate the introduction or conclusion.

  * **Endpoint**: `POST /projects/{project_id}/finalize`
  * **Body**: Specify whether you want an `introduction` or `conclusion`.

<!-- end list -->

```bash
curl -X POST "http://127.0.0.1:8000/projects/YOUR_PROJECT_ID/finalize" \
-H "Content-Type: application/json" \
-d '{
  "task_type": "introduction"
}'
```

-----

## Project Structure

The project follows a modular, feature-based structure to separate concerns.

```
src/
├── core/         # Cross-cutting concerns: config, database, task queue
├── crew/         # AI agent logic, services, workers, and API routes
├── project/      # Data models, services, and API routes for the book itself
├── main.py       # Main FastAPI application entry point
└── ...
```

-----

## Contributing

Contributions are welcome\! Please follow these steps:

1.  Fork the repository.
2.  Create a new feature branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes and commit them (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature-name`).
5.  Open a Pull Request.

-----

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.