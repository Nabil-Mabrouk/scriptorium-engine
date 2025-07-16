<template>
  <div>
    <AppHeader />
    <main class="max-w-7xl mx-auto px-4 py-6">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppHeader from './AppHeader.vue';
</script>