<template>
  <div class="p-4 bg-black/20 rounded-lg mt-4">
    <h3 class="text-lg font-semibold text-slate-300 mb-3">Draft Chapter Outline</h3>
    <div v-for="(chapter, index) in editableChapters" :key="index" class="mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
      <div class="flex justify-between items-center mb-4">
        <label class="font-semibold text-slate-300">Chapter {{ chapter.chapter_number }}</label>
        <button @click="removeChapter(index)" class="text-red-400 hover:text-red-300 text-sm">Remove</button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input type="text" v-model="chapter.title" placeholder="Chapter Title" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md">
        <input type="text" v-model="chapter.suggested_agent" placeholder="Suggested Agent" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md">
      </div>
      <div class="mt-4">
        <label class="block text-sm font-medium text-slate-400 mb-1">Brief: Thesis Statement</label>
        <textarea v-model="chapter.brief.thesis_statement" rows="2" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"></textarea>
      </div>
       <div class="mt-2">
        <label class="block text-sm font-medium text-slate-400 mb-1">Brief: Narrative Arc</label>
        <textarea v-model="chapter.brief.narrative_arc" rows="2" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"></textarea>
      </div>
    </div>
    
    <div class="flex justify-between mt-6">
      <button @click="addChapter" class="px-4 py-2 rounded-md font-semibold border border-slate-600 hover:bg-slate-700 transition-colors">+ Add Chapter</button>
      <button @click="submitFinalization" class="px-6 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 transition-colors">Finalize Chapter Structure</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useProjectStore } from '@/stores/project';

// Re-define interfaces for strong typing within the component
interface ChapterBrief { thesis_statement: string; narrative_arc: string; required_inclusions: string[]; key_questions_to_answer: string[]; }
interface Chapter { chapter_number: number; title: string; brief: ChapterBrief; suggested_agent: string; }

const props = defineProps<{
  projectId: string;
  partId: string;
  draftChapters: { chapters: Chapter[] };
}>();

const projectStore = useProjectStore();
const editableChapters = ref<Chapter[]>([]);

watch(() => props.draftChapters, (newDraft) => {
  editableChapters.value = JSON.parse(JSON.stringify(newDraft.chapters || []));
}, { immediate: true, deep: true });

const addChapter = () => {
  const nextChapterNumber = editableChapters.value.length > 0 ? Math.max(...editableChapters.value.map(c => c.chapter_number)) + 1 : 1;
  editableChapters.value.push({
    chapter_number: nextChapterNumber, title: '', suggested_agent: '',
    brief: { thesis_statement: '', narrative_arc: '', required_inclusions: [], key_questions_to_answer: [] },
  });
};

const removeChapter = (index: number) => {
  editableChapters.value.splice(index, 1);
};

const submitFinalization = async () => {
  const finalChapters = { chapters: editableChapters.value.map((chap, index) => ({ ...chap, chapter_number: index + 1 })) };
  if (confirm('Are you sure you want to finalize the chapters for this part?')) {
    await projectStore.finalizeChapters(props.partId, finalChapters);
  }
};
</script>