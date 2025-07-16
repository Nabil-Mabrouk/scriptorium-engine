<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="open"
        class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
        @click.self="$emit('close')"
      >
        <div
          class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col"
        >
          <!-- Header -->
          <header class="px-6 py-4 border-b">
            <h3 class="text-lg font-bold">
              Validate Chapters – Part {{ partNumber }}
            </h3>
          </header>

          <!-- Scrollable list -->
          <main class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            <div
              v-for="(ch, idx) in editableChapters"
              :key="idx"
              class="border rounded p-3 space-y-2"
            >
              <!-- Title -->
              <label class="block text-sm font-semibold">Title</label>
              <input
                v-model="ch.title"
                class="w-full border rounded px-2 py-1 text-sm"
              />

              <!-- Chapter Number -->
              <label class="block text-sm font-semibold">Number</label>
              <input
                v-model.number="ch.chapter_number"
                type="number"
                min="1"
                class="w-20 border rounded px-2 py-1 text-sm"
              />

              <!-- Suggested Agent -->
              <label class="block text-sm font-semibold">Agent</label>
              <select v-model="ch.suggested_agent" class="border rounded px-2 py-1 text-sm">
                <option value="Historian AI">Historian AI</option>
                <option value="Technologist AI">Technologist AI</option>
                <option value="Philosopher AI">Philosopher AI</option>
                <option value="Theorist AI">Theorist AI</option>
              </select>

              <!-- Brief (JSON) -->
              <label class="block text-sm font-semibold">Brief (JSON)</label>
              <textarea
                v-model="briefJSON[idx]"
                rows="4"
                class="w-full border rounded px-2 py-1 text-xs font-mono"
                spellcheck="false"
              />
            </div>
          </main>

          <!-- Footer -->
          <footer class="px-6 py-4 border-t flex justify-end space-x-2">
            <BaseButton variant="secondary" @click="$emit('close')">
              Cancel
            </BaseButton>
            <BaseButton @click="save">Save & Close</BaseButton>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watchEffect } from 'vue';
import BaseButton from '@/components/base/BaseButton.vue';

interface ChapterDraft {
  chapter_number: number;
  title: string;
  brief: any;
  suggested_agent: string;
}

const props = defineProps<{
  open: boolean;
  chapters: ChapterDraft[];
  partNumber: number;
}>();

const emit = defineEmits<{
  save: [payload: { chapters: ChapterDraft[] }];
  close: [];
}>();

// Deep-copy so we can mutate without side-effects
const editableChapters = computed<ChapterDraft[]>(() =>
  JSON.parse(JSON.stringify(props.chapters))
);

// Stringified brief for each chapter (editable textarea)
const briefJSON = computed<string[]>(() =>
  editableChapters.value.map((c) => JSON.stringify(c.brief, null, 2))
);

const save = () => {
  const result = editableChapters.value.map((c, idx) => ({
    ...c,
    brief: JSON.parse(briefJSON.value[idx]),
  }));
  emit('save', { chapters: result });
};
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>