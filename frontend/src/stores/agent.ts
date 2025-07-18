// frontend/src/stores/agent.ts
import { defineStore } from 'pinia';
import apiClient from '@/lib/api'; // Use our centralized API client
import type { components } from '@/lib/types'; // Import component types from OpenAPI spec

// Define a type for the array of agent names from the backend
type AgentNames = components['schemas']['ChapterRead']['suggested_agent'][]; // Or string[], but this is more precise if `suggested_agent` is an enum in the spec.
// Given the backend returns List[str], `string[]` is fine, but using types from openapi-typescript is best practice.
// In your `src/lib/types.ts` the `get_agent_names` operation should yield `List[str]` as a response.
// Let's assume it maps to `string[]` for now, or check your `types.ts` for the exact response type of `/crew/agents`.
// If it's `operations['get_agent_names_crew_agents_get']['responses']['200']['content']['application/json']`
// that would be the most accurate type. For simplicity here, we'll use `string[]`.

export const useAgentStore = defineStore('agent', {
  state: () => ({
    agentNames: [] as string[], // Store the list of agent names
    isLoading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchAgentNames() {
      if (this.agentNames.length > 0 && !this.isLoading) {
        // Already fetched and not currently loading, so return cached data
        return;
      }
      this.isLoading = true;
      this.error = null;
      try {
        console.log('➡️ [API Request] GET /crew/agents');
        const response = await apiClient.get<string[]>('/crew/agents'); // Expecting a string array
        console.log('✅ [API Response] Fetched agent names:', response.data);
        this.agentNames = response.data;
      } catch (err: any) {
        console.error('❌ [API Error] Failed to fetch agent names:', err);
        this.error = err.message || 'Failed to fetch agent names.';
      } finally {
        this.isLoading = false;
      }
    },
  },
  getters: {
    // Optionally provide a getter for ease of use
    availableAgents: (state) => state.agentNames,
  },
});