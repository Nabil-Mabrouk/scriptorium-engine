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

        <div v-else-if="project.status === 'PARTS_PENDING_VALIDATION' && project.structured_outline">
          <h3 class="text-teal-400 font-semibold mb-3">Draft Ready for Review</h3>
          <PartEditor 
            :project-id="project.id"
            :draft-parts="project.structured_outline" 
          />
        </div>

        <div v-else-if="project.parts && project.parts.length > 0">
          <h3 class="text-teal-400 font-semibold mb-4">Finalized Structure</h3>
          <div class="space-y-4">
            <div v-for="part in project.parts" :key="part.id" class="p-4 bg-slate-900 rounded-md">
              <div class="flex justify-between items-center">
                <div>
                  <strong class="text-white">Part {{ part.part_number }}:</strong>
                  <span class="ml-2 text-slate-300">{{ part.title }}</span>
                </div>
                <button 
                  v-if="project.status === 'PARTS_VALIDATED'"
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
              </div>
              
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
                      <button
                        v-if="!chapter.content && chapter.status !== 'BRIEF_COMPLETE'"
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
                    </div>
                  </summary>

                  <div v-if="chapter.brief" class="p-4 border-t border-slate-700 text-xs space-y-3">
                    <div v-for="(value, key) in chapter.brief" :key="key">
                      <h4 class="font-semibold text-slate-400 capitalize">{{ key.replace(/_/g, ' ') }}</h4>
                      <p class="mt-1 pl-2 border-l-2 border-slate-600 text-slate-300 whitespace-pre-wrap">{{ value }}</p>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
          
          <div v-if="project.status === 'CHAPTERS_PENDING_VALIDATION' && project.structured_outline && project.structured_outline.chapters">
            <ChapterEditor
              :project-id="project.id"
              :part-id="selectedPartId" 
              :draft-chapters="project.structured_outline"
            />
          </div>
        </div>
      </div>

    </div>
  </AppLayout>
</template>
<script setup lang="ts">
import { onMounted, computed, ref } from 'vue';
import { useProjectStore } from '@/stores/project';
import AppLayout from '@/components/layout/AppLayout.vue';
import PartEditor from '@/components/features/projects/PartEditor.vue';
import ChapterEditor from '@/components/features/projects/ChapterEditor.vue';

const props = defineProps<{ id: string }>();
const projectStore = useProjectStore();

// This computed property points to the single project being viewed
const project = computed(() => projectStore.activeProject);

// This state tracks which part we are currently detailing chapters for
const selectedPartId = ref<string>('');

// Fetch the project data when the page loads
onMounted(() => {
  projectStore.fetchProjectById(props.id);
});

// Add this new handler function
const handleGenerateContent = async (chapterId: string) => {
  await projectStore.generateChapterContent(chapterId);
};

// Handler to trigger the parts generation AI
const handleGenerateParts = async () => {
  await projectStore.generateParts(props.id);
};

// Handler to trigger the chapters generation AI for a specific part
const handleGenerateChapters = async (partId: string) => {
  selectedPartId.value = partId; // Keep track of which part was clicked
  await projectStore.generateChapters(partId);
};
</script>