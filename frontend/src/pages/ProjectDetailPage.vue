<template>
  <AppLayout>
    <div v-if="projectStore.isLoading && !project">Loading Project...</div>
    <div v-else-if="projectStore.error" class="text-red-400">{{ projectStore.error }}</div>
    <div v-else-if="project" class="space-y-8">

      <div>
        <h1 class="text-3xl font-bold text-teal-400 mb-2">{{ `Project: ${project.id.substring(0, 8)}...` }}</h1>
        <span class="inline-block px-3 py-1 text-xs font-semibold rounded-full bg-slate-700 text-slate-300 capitalize">
          {{ project.status.replace(/_/g, ' ').toLowerCase() }}
        </span>
      </div>

      <div class="p-6 bg-slate-800 rounded-lg">
        <h2 class="text-xl font-semibold mb-3">Raw Blueprint</h2>
        <p class="text-slate-300 whitespace-pre-wrap">{{ project.raw_blueprint }}</p>
      </div>
      
      <div class="p-6 bg-slate-800 rounded-lg">
        <h2 class="text-xl font-semibold mb-4">Book Structure</h2>

        <!-- Phase 1: RAW_IDEA -> Generate Part Outline -->
        <div v-if="project.status === 'RAW_IDEA'">
          <div class="text-center p-4 border-2 border-dashed border-slate-700 rounded-lg">
            <p class="text-slate-400 mb-4">This project is a raw idea. The first step is to generate the part outline.</p>
            <button 
              @click="handleGenerateParts"
              :disabled="projectStore.processingIds.has(project.id)"
              class="px-4 py-2 rounded-md font-semibold transition-colors"
              :class="{
                'bg-teal-600 hover:bg-teal-500': !projectStore.processingIds.has(project.id),
                'bg-slate-500 cursor-not-allowed': projectStore.processingIds.has(project.id)
              }"
            >
              {{ projectStore.processingIds.has(project.id) ? 'Processing...' : 'Generate Part Outline' }}
            </button>
          </div>
        </div>

        <!-- Phase 1.5: PARTS_PENDING_VALIDATION -> Edit Part Outline -->
        <div v-else-if="project.status === 'PARTS_PENDING_VALIDATION' && draftPartsOutline">
          <h3 class="text-teal-400 font-semibold mb-3">Draft Parts Ready for Review</h3>
          <PartEditor 
            :project-id="project.id"
            :draft-parts="draftPartsOutline" 
          />
        </div>

        <!-- Display Finalized Parts and Chapters -->
        <div v-else-if="project.parts && project.parts.length > 0">
          <h3 class="text-teal-400 font-semibold mb-4">Finalized Structure</h3>
          <div class="space-y-4">
            <div v-for="part in project.parts" :key="part.id" class="p-4 bg-slate-900 rounded-md">
              <div class="flex justify-between items-center">
                <div>
                  <strong class="text-white">Part {{ part.part_number }}:</strong>
                  <span class="ml-2 text-slate-300">{{ part.title }}</span>
                  <!-- NEW: Display Part Summary -->
                  <p class="text-sm text-slate-400 mt-1 pl-4 border-l-2 border-slate-700">{{ part.summary }}</p>
                </div>
                <!-- Phase 2: PARTS_VALIDATED -> Generate Chapters for a Part -->
                <button 
                  v-if="project.status === 'PARTS_VALIDATED' && !part.chapters?.length"
                  @click="handleGenerateChapters(part.id)"
                  :disabled="projectStore.processingIds.has(part.id)"
                  class="px-3 py-1 text-sm rounded-md font-semibold transition-colors"
                  :class="{
                    'bg-teal-600 hover:bg-teal-500': !projectStore.processingIds.has(part.id),
                    'bg-slate-500 cursor-not-allowed': projectStore.processingIds.has(part.id)
                  }"
                >
                  {{ projectStore.processingIds.has(part.id) ? 'Processing...' : 'Detail Chapters' }}
                </button>
                <!-- Alternatively, if chapters exist but need re-detailing: -->
                <button 
                  v-else-if="project.status === 'PARTS_VALIDATED' && part.chapters?.length && !projectStore.processingIds.has(part.id)"
                  @click="handleGenerateChapters(part.id)"
                  class="px-3 py-1 text-sm rounded-md font-semibold bg-blue-600 hover:bg-blue-500 transition-colors"
                >
                  Re-Detail Chapters
                </button>
              </div>
              
              <!-- Display Finalized Chapters for the Part -->
              <div v-if="part.chapters && part.chapters.length > 0" class="mt-4 pl-6 border-l-2 border-slate-700 space-y-3">
                <details v-for="chapter in part.chapters" :key="chapter.id" class="bg-slate-800/50 rounded-lg">
                  <summary class="p-2 cursor-pointer hover:bg-slate-700/50 rounded-lg list-none">
                    <div class="flex justify-between items-center">
                      <p class="text-sm text-slate-300 font-medium">
                        <strong>Ch {{ chapter.chapter_number }}:</strong> {{ chapter.title }}
                        <span class="ml-2 text-xs capitalize px-2 py-0.5 rounded-full bg-slate-700 text-slate-400">
                          {{ chapter.status.replace(/_/g, ' ') }}
                        </span>
                      </p>
                      <!-- Phase 3: BRIEF_COMPLETE -> Generate Content -->
                      <button
                        v-if="chapter.status === 'BRIEF_COMPLETE'"
                        @click.prevent="handleGenerateContent(chapter.id)"
                        :disabled="projectStore.processingIds.has(chapter.id)"
                        class="px-3 py-1 text-xs rounded-md font-semibold transition-colors z-10"
                        :class="{
                          'bg-sky-600 hover:bg-sky-500': !projectStore.processingIds.has(chapter.id),
                          'bg-slate-500 cursor-not-allowed': projectStore.processingIds.has(chapter.id)
                        }"
                      >
                        {{ projectStore.processingIds.has(chapter.id) ? 'Processing...' : 'Generate Content' }}
                      </button>
                      <!-- TODO: Add buttons for Review Content, Analyze Transition, etc. based on status -->
                    </div>
                  </summary>

                  <!-- Display Chapter Brief -->
                  <div v-if="chapter.brief" class="p-4 border-t border-slate-700 text-xs space-y-3">
                    <div v-for="(value, key) in chapter.brief" :key="key">
                      <h4 class="font-semibold text-slate-400 capitalize">{{ formatBriefKey(key) }}</h4>
                      <p class="mt-1 pl-2 border-l-2 border-slate-600 text-slate-300 whitespace-pre-wrap">
                        {{ formatBriefValue(value) }}
                      </p>
                    </div>
                  </div>
                  <!-- Display Chapter Content if available -->
                  <div v-if="chapter.content" class="p-4 border-t border-slate-700 text-sm space-y-3">
                    <h4 class="font-semibold text-slate-400">Content</h4>
                    <p class="mt-1 pl-2 border-l-2 border-slate-600 text-slate-300 whitespace-pre-wrap">{{ chapter.content }}</p>
                  </div>
                </details>
              </div>

              <!-- Phase 2.5: CHAPTERS_PENDING_VALIDATION -> Edit Chapter Outline for this Part -->
              <!-- Render ChapterEditor only if project status allows and if it's the currently selected part -->
              <div v-if="project.status === 'CHAPTERS_PENDING_VALIDATION' && part.id === selectedPartId && draftChaptersOutline">
                <h3 class="text-teal-400 font-semibold mb-3 mt-4">Draft Chapters for Part "{{ part.title }}" Ready for Review</h3>
                <ChapterEditor
                  :project-id="project.id"
                  :part-id="selectedPartId" 
                  :draft-chapters="draftChaptersOutline"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, computed, ref, watch } from 'vue';
import { useProjectStore } from '@/stores/project';
import AppLayout from '@/components/layout/AppLayout.vue';
import PartEditor from '@/components/features/projects/PartEditor.vue';
import ChapterEditor from '@/components/features/projects/ChapterEditor.vue';

// IMPORTER: Import necessary types from the auto-generated types.ts
import type { 
  ProjectDetailRead, 
  PartListOutline, 
  ChapterListOutline,
  ChapterRead // For content property
} from '@/lib/types';


const props = defineProps<{ id: string }>();
const projectStore = useProjectStore();

// This computed property points to the single project being viewed
const project = computed<ProjectDetailRead | null>(() => projectStore.activeProject);

// This state tracks which part we are currently detailing chapters for editing
const selectedPartId = ref<string>('');

// Fetch the project data when the page loads
onMounted(() => {
  projectStore.fetchProjectById(props.id);
});

// Watch for project changes to update selectedPartId if status changes to chapter detailing
watch(() => project.value?.status, (newStatus) => {
  if (newStatus === 'CHAPTERS_PENDING_VALIDATION' && project.value?.structured_outline) {
    // Attempt to find the part ID from the structured_outline if it's there
    // This is a heuristic: assuming structured_outline will have one key for the part being detailed
    const partIds = Object.keys(project.value.structured_outline);
    if (partIds.length > 0 && !selectedPartId.value) { // Only set if not already set by button click
      selectedPartId.value = partIds[0]; 
    }
  }
}, { immediate: true });


// NEW COMPUTED PROPERTIES for draft outlines
const draftPartsOutline = computed<PartListOutline | null>(() => {
  // Check if structured_outline exists and contains a 'parts' array (characteristic of PartListOutline)
  if (project.value?.status === 'PARTS_PENDING_VALIDATION' && project.value.structured_outline && 'parts' in project.value.structured_outline) {
    return project.value.structured_outline as PartListOutline;
  }
  return null;
});

const draftChaptersOutline = computed<ChapterListOutline | null>(() => {
  // Check if structured_outline exists, we have a selectedPartId, and that part ID exists in the outline
  if (project.value?.status === 'CHAPTERS_PENDING_VALIDATION' && project.value.structured_outline && selectedPartId.value) {
    const chapterOutlineData = project.value.structured_outline[selectedPartId.value];
    // Further check if it looks like a ChapterListOutline
    if (chapterOutlineData && 'chapters' in chapterOutlineData) {
      return chapterOutlineData as ChapterListOutline;
    }
  }
  return null;
});


// Helper function to format brief keys (e.g., "required_inclusions" -> "Required Inclusions")
const formatBriefKey = (key: string) => {
  return key.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};

// Helper function to format brief values (arrays as bullet points)
const formatBriefValue = (value: any) => {
  if (Array.isArray(value)) {
    return value.length > 0 ? value.map(item => `• ${item}`).join('\n') : 'N/A';
  }
  return value || 'N/A';
};


// Handler to trigger the parts generation AI
const handleGenerateParts = async () => {
  await projectStore.generateParts(props.id);
};

// Handler to trigger the chapters generation AI for a specific part
const handleGenerateChapters = async (partId: string) => {
  selectedPartId.value = partId; // Crucially, set the selected part ID before triggering generation
  await projectStore.generateChapters(partId);
};

// Add this new handler function
const handleGenerateContent = async (chapterId: string) => {
  await projectStore.generateChapterContent(chapterId);
};
</script>