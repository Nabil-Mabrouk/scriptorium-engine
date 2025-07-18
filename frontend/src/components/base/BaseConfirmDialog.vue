<template>
  <BaseModal
    :visible="uiStore.activeConfirmation !== null"
    @close="handleCancel"
    max-width="sm"
  >
    <template #header>
      <h2 class="text-xl font-bold text-slate-100">{{ uiStore.activeConfirmation?.title }}</h2>
    </template>

    <div class="text-slate-300 text-base">
      <p>{{ uiStore.activeConfirmation?.message }}</p>
    </div>

    <template #footer>
      <button
        type="button"
        @click="handleCancel"
        class="px-4 py-2 rounded-md bg-slate-700 hover:bg-slate-600 transition-colors"
      >
        {{ uiStore.activeConfirmation?.cancelText || 'Cancel' }}
      </button>
      <button
        type="button"
        @click="handleConfirm"
        class="px-4 py-2 rounded-md font-semibold bg-teal-600 hover:bg-teal-500 transition-colors"
      >
        {{ uiStore.activeConfirmation?.confirmText || 'Confirm' }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { useUiStore } from '@/stores/ui';
import BaseModal from './BaseModal.vue'; // Assuming BaseModal is in the same 'base' directory

const uiStore = useUiStore();

// Handle the "Confirm" action
const handleConfirm = () => {
  uiStore._resolveConfirmation(true); // Resolve the promise with true
};

// Handle the "Cancel" action (or modal close)
const handleCancel = () => {
  uiStore._resolveConfirmation(false); // Resolve the promise with false
};
</script>