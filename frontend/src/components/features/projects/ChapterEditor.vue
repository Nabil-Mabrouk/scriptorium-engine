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
        
        <!-- NEW: Suggested Agent as a dropdown -->
        <select
          v-model="chapter.suggested_agent"
          class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"
        >
          <option value="" disabled>Select Suggested Agent</option>
          <option v-for="agentName in agentStore.availableAgents" :key="agentName" :value="agentName">
            {{ agentName }}
          </option>
        </select>
      </div>
      <div class="mt-4">
        <label class="block text-sm font-medium text-slate-400 mb-1">Brief: Thesis Statement</label>
        <textarea v-model="chapter.brief.thesis_statement" rows="2" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"></textarea>
      </div>
       <div class="mt-2">
        <label class="block text-sm font-medium text-slate-400 mb-1">Brief: Narrative Arc</label>
        <textarea v-model="chapter.brief.narrative_arc" rows="2" class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"></textarea>
      </div>

      <div class="mt-2">
        <label class="block text-sm font-medium text-slate-400 mb-1">Brief: Required Inclusions (comma-separated)</label>
        <textarea
          v-model="chapter.brief.required_inclusions_string"
          @input="updateRequiredInclusions(chapter)"
          rows="2"
          class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"
          placeholder="e.g., AI ethics, technological singularity, human-machine symbiosis"
        ></textarea>
      </div>
      <div class="mt-2">
        <label class="block text-sm font-medium text-slate-400 mb-1">Brief: Key Questions to Answer (comma-separated)</label>
        <textarea
          v-model="chapter.brief.key_questions_to_answer_string"
          @input="updateKeyQuestionsToAnswer(chapter)"
          rows="2"
          class="w-full p-2 bg-slate-800 border border-slate-600 rounded-md"
          placeholder="e.g., How will AI impact employment?, What are the risks of unchecked AI development?"
        ></textarea>
      </div>

    </div>
    
    <div class="flex justify-between mt-6">
      <button @click="addChapter" class="px-4 py-2 rounded-md font-semibold border border-slate-600 hover:bg-slate-700 transition-colors">+ Add Chapter</button>
      <button @click="submitFinalization" class="px-6 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 transition-colors">Finalize Chapter Structure</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'; // Import onMounted
import { useProjectStore } from '@/stores/project';
import { useAgentStore } from '@/stores/agent'; // NEW: Import the new agent store

import type { ChapterOutline, ChapterListOutline, ChapterBrief } from '@/lib/types';

// Extend ChapterBrief type locally for the string versions of array fields
interface EditableChapterBrief extends ChapterBrief {
  required_inclusions_string?: string;
  key_questions_to_answer_string?: string;
}

// Extend ChapterOutline to use the editable brief and ensure it can hold the string versions
interface EditableChapterOutline extends ChapterOutline {
  brief: EditableChapterBrief;
}

const props = defineProps<{
  projectId: string;
  partId: string;
  draftChapters: ChapterListOutline; 
}>();

const projectStore = useProjectStore();
const agentStore = useAgentStore(); // NEW: Initialize the agent store
const editableChapters = ref<EditableChapterOutline[]>([]);

// Fetch agent names when the component mounts
onMounted(() => {
  agentStore.fetchAgentNames();
});

// Helper function to convert array to comma-separated string
const arrayToString = (arr: string[] | undefined) => (arr ? arr.join(', ') : '');
// Helper function to convert comma-separated string to array
const stringToArray = (str: string | undefined) => (str ? str.split(',').map(s => s.trim()).filter(s => s.length > 0) : []);


watch(() => props.draftChapters, (newDraft) => {
  editableChapters.value = JSON.parse(JSON.stringify(newDraft.chapters || []));
  editableChapters.value.forEach(chapter => {
    chapter.brief.required_inclusions_string = arrayToString(chapter.brief.required_inclusions);
    chapter.brief.key_questions_to_answer_string = arrayToString(chapter.brief.key_questions_to_answer);
    // Ensure suggested_agent is initialized to an empty string if null/undefined for dropdown default
    if (!chapter.suggested_agent) {
      chapter.suggested_agent = '';
    }
  });
}, { immediate: true, deep: true });

const addChapter = () => {
  const nextChapterNumber = editableChapters.value.length > 0 ? Math.max(...editableChapters.value.map(c => c.chapter_number)) + 1 : 1;
  editableChapters.value.push({
    chapter_number: nextChapterNumber, 
    title: '', 
    suggested_agent: '', // Default to empty string for dropdown
    brief: { 
      thesis_statement: '', 
      narrative_arc: '', 
      required_inclusions: [], 
      key_questions_to_answer: [],
      required_inclusions_string: '',
      key_questions_to_answer_string: ''
    } as EditableChapterBrief, 
  });
};

const removeChapter = (index: number) => {
  editableChapters.value.splice(index, 1);
};

const updateRequiredInclusions = (chapter: EditableChapterOutline) => {
  chapter.brief.required_inclusions = stringToArray(chapter.brief.required_inclusions_string);
};

const updateKeyQuestionsToAnswer = (chapter: EditableChapterOutline) => {
  chapter.brief.key_questions_to_answer = stringToArray(chapter.brief.key_questions_to_answer_string);
};


const submitFinalization = async () => {
  const chaptersToSend = editableChapters.value.map(chap => {
    const briefToSend: ChapterBrief = {
      thesis_statement: chap.brief.thesis_statement,
      narrative_arc: chap.brief.narrative_arc,
      required_inclusions: stringToArray(chap.brief.required_inclusions_string),
      key_questions_to_answer: stringToArray(chap.brief.key_questions_to_answer_string),
    };

    return {
      ...chap, 
      chapter_number: editableChapters.value.indexOf(chap) + 1, 
      brief: briefToSend, 
    };
  });

  const finalChapters: ChapterListOutline = { chapters: chaptersToSend };

  if (confirm('Are you sure you want to finalize the chapters for this part?')) {
    await projectStore.finalizeChapters(props.partId, finalChapters);
  }
};
</script>