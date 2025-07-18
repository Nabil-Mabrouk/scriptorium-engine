<template>
  <router-view />
  <NotificationContainer />
  <BaseConfirmDialog /> <!-- NEW: Add the confirmation dialog component here -->
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router';
import NotificationContainer from '@/components/layout/NotificationContainer.vue';
import BaseConfirmDialog from '@/components/base/BaseConfirmDialog.vue'; // NEW: Import the confirmation dialog
</script>