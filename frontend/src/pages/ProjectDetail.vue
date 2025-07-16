<template>
  <AppLayout>
    <div v-if="loading" class="text-center py-10">Loading project…</div>
    <div v-else-if="project">
      <!-- Job Banner -->
      <div
        v-if="jobStatus && jobStatus !== 'success'"
        class="fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded shadow z-50"
      >
        Job: {{ jobStatus }}
      </div>

      <h2 class="text-2xl font-bold mb-2">Project Detail</h2>
      <p class="mb-4 text-sm text-gray-600">
        Status: {{ project.status }} | Cost: ${{ project.total_cost }}
      </p>

      <!-- PHASE 1 -->
      <section class="mb-6">
        <h3 class="text-lg font-semibold mb-1">Phase 1 – Parts</h3>
        <div class="space-x-2">
          <BaseButton v-if="project.status === 'RAW_IDEA'" @click="runParts">
            Generate Parts
          </BaseButton>
          <BaseButton
            v-if="project.status === 'PARTS_PENDING_VALIDATION'"
            @click="openPartsModal"
          >
            Validate Parts
          </BaseButton>
        </div>
      </section>

      <!-- Validate Parts Modal -->
      <ValidatePartsModal
        :open="showValidateParts"
        :parts="project.structured_outline?.parts || []"
        @save="saveParts"
        @close="showValidateParts = false"
      />

      <!-- PHASE 2+ -->
      <section v-if="project.parts?.length" class="space-y-6">
        <div
          v-for="part in project.parts"
          :key="part.id"
          class="border rounded p-4"
        >
          <h4 class="font-bold">
            Part {{ part.part_number }}: {{ part.title }}
          </h4>
          <p class="text-sm mb-2">{{ part.summary }}</p>

          <div class="space-x-2 mb-2">
              <button class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                Test Button
                </button>
            <BaseButton
               v-if="project.status === 'PARTS_VALIDATED'"
               size="sm"
              @click="runChapters(part.id)"
            >
               Generate Chapters
            </BaseButton>
            <BaseButton
              v-if="part.status === 'CHAPTERS_PENDING_VALIDATION'"
              size="sm"
              @click="openChaptersModal(part)"
            >
              Validate Chapters
            </BaseButton>
          </div>

          <!-- Chapters -->
          <ul v-if="part.chapters?.length" class="space-y-1 text-sm">
            <li
              v-for="ch in part.chapters"
              :key="ch.id"
              class="flex items-center justify-between"
            >
              <span>{{ ch.chapter_number }}. {{ ch.title }} ({{ ch.status }})</span>
              <div class="space-x-1">
                <BaseButton
                  v-if="ch.status === 'BRIEF_COMPLETE'"
                  size="xs"
                  @click="runChapter(ch.id)"
                >
                  Write
                </BaseButton>
                <BaseButton
                  v-if="ch.status === 'CONTENT_GENERATED'"
                  size="xs"
                  @click="runTransition(ch.id)"
                >
                  Transition
                </BaseButton>
              </div>
            </li>
          </ul>
        </div>
      </section>

      <!-- Validate Chapters Modal -->
      <ValidateChaptersModal
        :open="showValidateChapters"
        :chapters="currentChapters"
        :part-number="currentPartNumber"
        @save="saveChapters"
        @close="showValidateChapters = false"
      />

      <!-- PHASE 5 – Finalize -->
      <section v-if="project.status === 'COMPLETE_CHAPTERS'" class="mt-8">
        <h3 class="text-lg font-semibold mb-2">Phase 5 – Finalize Book</h3>
        <div class="space-x-2">
          <BaseButton @click="finalize('introduction')">
            Generate Introduction
          </BaseButton>
          <BaseButton @click="finalize('conclusion')">
            Generate Conclusion
          </BaseButton>
        </div>
      </section>
    </div>

    <div v-else class="text-center py-10">Project not found</div>
  </AppLayout>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import AppLayout from '@/components/layout/AppLayout.vue';
import BaseButton from '@/components/base/BaseButton.vue';
import ValidatePartsModal from '@/components/features/ValidatePartsModal.vue';
import ValidateChaptersModal from '@/components/features/ValidateChaptersModal.vue';
import {
  fetchProject,
  finalizeParts,
  generateChapters,
  finalizeChapters,
  generateChapter,
  analyzeTransition,
  finalizeBook,
  api, // reuse for polling
} from '@/lib/api';

const route = useRoute();
const project = ref();
const loading = ref(true);

/* --- Modals --- */
const showValidateParts = ref(false);
const showValidateChapters = ref(false);
const currentChapters = ref([]);
const currentPartNumber = ref(0);

/* --- Job polling --- */
const jobStatus = ref<'queued' | 'running' | 'success' | 'error' | null>(null);
let pollTimer: number | null = null;

const startPoll = (jobId: string) => {
  jobStatus.value = 'queued';
  pollTimer = window.setInterval(async () => {
    try {
      const { data } = await api.get(`/crew/status/${jobId}`);
      jobStatus.value = data.status;
      if (['success', 'error'].includes(data.status)) {
        clearInterval(pollTimer!);
        await loadProject(); // refresh after job done
        jobStatus.value = null;
      }
    } catch {
      jobStatus.value = 'error';
      clearInterval(pollTimer!);
    }
  }, 2000);
};

/* --- Load project --- */
const loadProject = async () => {
  loading.value = true;
  project.value = await fetchProject(route.params.id as string);
  loading.value = false;
};

/* --- Phase 1 --- */
const runParts = async () => {
  const { job_id } = await api.post(`/crew/generate-parts/${project.value.id}`);
  startPoll(job_id);
};
const openPartsModal = () => (showValidateParts.value = true);
const saveParts = async (parts: any) => {
  await finalizeParts(project.value.id, { parts });
  showValidateParts.value = false;
  await loadProject();
};

/* --- Phase 2 --- */
const runChapters = async (partId: string) => {
  const { job_id } = await generateChapters(partId);
  startPoll(job_id);
};
const openChaptersModal = (part: any) => {
  currentChapters.value = part.chapters || [];
  currentPartNumber.value = part.part_number;
  showValidateChapters.value = true;
};
const saveChapters = async ({ chapters }: { chapters: any }) => {
  await finalizeChapters(currentChapters.value[0].part.id, { chapters });
  showValidateChapters.value = false;
  await loadProject();
};

/* --- Phase 3 & 4 --- */
const runChapter = async (chapterId: string) => {
  const { job_id } = await generateChapter(chapterId);
  startPoll(job_id);
};
const runTransition = async (chapterId: string) => {
  const { job_id } = await analyzeTransition(chapterId);
  startPoll(job_id);
};

/* --- Phase 5 --- */
const finalize = async (type: 'introduction' | 'conclusion') => {
  const { job_id } = await finalizeBook(project.value.id, type);
  startPoll(job_id);
};

onMounted(loadProject);
</script>