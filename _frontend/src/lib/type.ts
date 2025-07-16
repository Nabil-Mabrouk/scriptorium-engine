// You can auto-generate this with openapi-typescript
// npx openapi-typescript http://localhost:8000/openapi.json --output src/lib/types.ts

export interface ProjectRead {
  id: string;
  raw_blueprint: string;
  status: string;
  structured_outline?: Record<string, any>;
  total_cost: number;
}

export interface PartRead {
  id: string;
  part_number: number;
  title: string;
  summary?: string;
}

export interface ChapterRead {
  id: string;
  chapter_number: number;
  title: string;
  status: string;
  suggested_agent?: string;
  part: PartRead;
}