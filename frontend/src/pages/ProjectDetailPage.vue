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
                  <p class="text-sm text-slate-400 mt-1 pl-4 border-l-2 border-slate-700">{{ part.summary }}</p>
                </div>
                
                <!-- Buttons for Chapter Detailing / Re-detailing / Processing -->
                <div class="flex-shrink-0">
                    <button 
                        v-if="part.status === 'DEFINED' && !projectStore.processingIds.has(part.id)"
                        @click="handleGenerateChapters(part.id)"
                        class="px-3 py-1 text-sm rounded-md font-semibold transition-colors bg-teal-600 hover:bg-teal-500"
                    >
                        Detail Chapters
                    </button>
                    <button
                        v-else-if="projectStore.processingIds.has(part.id)"
                        class="px-3 py-1 text-sm rounded-md font-semibold transition-colors bg-slate-500 cursor-not-allowed"
                        disabled
                    >
                        Processing...
                    </button>
                    <button 
                        v-else-if="part.status === 'CHAPTERS_VALIDATED' && !projectStore.processingIds.has(part.id)"
                        @click="handleGenerateChapters(part.id)"
                        class="px-3 py-1 text-sm rounded-md font-semibold bg-blue-600 hover:bg-blue-500 transition-colors"
                    >
                        Re-Detail Chapters
                    </button>
                    <button
                        v-else-if="part.status === 'CHAPTERS_PENDING_VALIDATION' && part.id !== selectedPartId"
                        @click="selectedPartId = part.id"
                        class="px-3 py-1 text-sm rounded-md font-semibold bg-blue-600 hover:bg-blue-500 transition-colors"
                    >
                        Review Chapters
                    </button>
                </div>
              </div>
              
              <!-- Display Finalized Chapters for the Part -->
              <div v-if="part.chapters && part.chapters.length > 0 && part.status === 'CHAPTERS_VALIDATED'" class="mt-4 pl-6 border-l-2 border-slate-700 space-y-3">
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
              <!-- Render ChapterEditor only if the part's status is PENDING_VALIDATION and it's the currently selected part -->
              <div v-if="part.status === 'CHAPTERS_PENDING_VALIDATION' && part.id === selectedPartId">
                <h3 class="text-teal-400 font-semibold mb-3 mt-4">Draft Chapters for Part "{{ part.title }}" Ready for Review</h3>
                <ChapterEditor
                  :project-id="project.id"
                  :part-id="selectedPartId" 
                  :draft-chapters="getDraftChaptersOutlineForPart(selectedPartId)"
                />
              </div>
              <!-- Section for when chapters are pending validation, but this isn't the selected part -->
              <div v-else-if="part.status === 'CHAPTERS_PENDING_VALIDATION' && part.id !== selectedPartId" class="text-center p-4 border-2 border-dashed border-slate-700 rounded-lg mt-4">
                  <p class="text-slate-400 mb-4">Chapters for this part are pending validation.</p>
                  <button @click="selectedPartId = part.id" class="px-4 py-2 rounded-md font-semibold bg-blue-600 hover:bg-blue-500 transition-colors">
                      Review Chapters
                  </button>
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
import { useUiStore } from '@/stores/ui'; 

import type { 
  ProjectDetailRead, 
  PartListOutline, 
  ChapterListOutline,
  ChapterRead 
} from '@/lib/types';


const props = defineProps<{ id: string }>();
const projectStore = useProjectStore();
const uiStore = useUiStore();

const project = computed<ProjectDetailRead | null>(() => projectStore.activeProject);

const selectedPartId = ref<string>('');

onMounted(async () => {
  console.log('--- ProjectDetailPage mounted ---');
  await projectStore.fetchProjectById(props.id);
  console.log('Project data fetched on mount. Current project value:', JSON.parse(JSON.stringify(project.value)));
  project.value?.parts.forEach(part => {
    console.log(`[OnMount] Part ${part.part_number} (${part.id.substring(0,8)}...): status=${part.status}, processing=${projectStore.processingIds.has(part.id)}`);
  });
  console.log('ProjectStore.processingIds on mount:', Array.from(projectStore.processingIds));
});

watch(() => project.value, (newProject) => {
  console.log('--- Project object updated via watcher ---');
  console.log('New project value in watcher:', JSON.parse(JSON.stringify(newProject)));
  if (newProject) { // Removed '&& newProject.structured_outline' as drafts are now separate fields
    // If a part is in CHAPTERS_PENDING_VALIDATION, ensure selectedPartId points to it.
    const pendingPart = newProject.parts.find(p => p.status === 'CHAPTERS_PENDING_VALIDATION');
    if (pendingPart && selectedPartId.value !== pendingPart.id) {
      selectedPartId.value = pendingPart.id;
      uiStore.showInfoToast(`Chapters for Part "${pendingPart.title}" are ready for review!`);
    } else if (!pendingPart && newProject.status !== 'PARTS_PENDING_VALIDATION') {
      selectedPartId.value = '';
    }
  }
  newProject?.parts.forEach(part => {
    console.log(`[Watch] Part ${part.part_number} (${part.id.substring(0,8)}...): status=${part.status}, processing=${projectStore.processingIds.has(part.id)}`);
  });
  console.log('ProjectStore.processingIds in watcher:', Array.from(projectStore.processingIds));

}, { immediate: true, deep: true });


const draftPartsOutline = computed<PartListOutline | null>(() => {
  // NEW: Check project.value.draft_parts_outline directly
  if (project.value?.draft_parts_outline) {
    return project.value.draft_parts_outline as PartListOutline;
  }
  return null;
});


// NEW: Helper function to get chapter outline for a specific part (now correctly checking draft_chapters_outline)
const getDraftChaptersOutlineForPart = (partId: string): ChapterListOutline | null => {
  console.log(`[getDraftChaptersOutlineForPart] Requested for part ID: ${partId}`);
  console.log(`[getDraftChaptersOutlineForPart] Current project.value.draft_chapters_outline:`, JSON.parse(JSON.stringify(project.value?.draft_chapters_outline || {})));

  // NEW: Access nested 'draft_chapters_outline' and then the partId within it
  if (project.value?.draft_chapters_outline) {
    const draftChaptersMap = project.value.draft_chapters_outline as Record<string, any>;
    if (draftChaptersMap && draftChaptersMap[partId]) {
      const chapterOutlineData = draftChaptersMap[partId];
      if (chapterOutlineData && 'chapters' in chapterOutlineData) {
        console.log(`[getDraftChaptersOutlineForPart] Found and returning draft chapters for part ID ${partId}.`);
        return chapterOutlineData as ChapterListOutline;
      } else {
        console.log(`[getDraftChaptersOutlineForPart] Found draft_chapters_outline[${partId}], but it does not contain 'chapters' property.`);
      }
    } else {
      console.log(`[getDraftChaptersOutlineForPart] draft_chapters_outline does not contain key for part ID ${partId}.`);
    }
  } else {
    console.log(`[getDraftChaptersOutlineForPart] draft_chapters_outline is null or undefined.`);
  }
  return null;
};


const formatBriefKey = (key: string) => {
  return key.replace(/_/g, ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
};

const formatBriefValue = (value: any) => {
  if (Array.isArray(value)) {
    return value.length > 0 ? value.map(item => `• ${item}`).join('\n') : 'N/A';
  }
  return value || 'N/A';
};


const handleGenerateParts = async () => {
  console.log('handleGenerateParts: Initiating part generation.');
  await projectStore.generateParts(props.id);
  console.log('handleGenerateParts: Part generation action dispatched.');
};

const handleGenerateChapters = async (partId: string) => {
  console.log(`handleGenerateChapters: Initiating chapter generation for part: ${partId}`);
  const part = project.value?.parts.find(p => p.id === partId);
  console.log(`handleGenerateChapters: Part ${partId.substring(0,8)}... status before API call: ${part?.status}`);
  console.log(`handleGenerateChapters: processingIds before API call: ${Array.from(projectStore.processingIds)}`);

  selectedPartId.value = partId;
  await projectStore.generateChapters(partId);

  console.log(`handleGenerateChapters: Chapter generation action dispatched. processingIds: ${Array.from(projectStore.processingIds)}`);
};

const handleGenerateContent = async (chapterId: string) => {
  console.log(`handleGenerateContent: Initiating content generation for chapter: ${chapterId}`);
  await projectStore.generateChapterContent(chapterId);
  console.log('handleGenerateContent: Content generation action dispatched.');
};
</script>