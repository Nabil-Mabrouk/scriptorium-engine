<template>
  <div class="flex h-screen bg-slate-900 text-slate-200">
    <aside class="w-64 flex-shrink-0 bg-black/30 p-4">
      <h1 class="text-2xl font-bold text-white">Scriptorium</h1>
      <nav class="mt-8">
        <router-link
          to="/"
          class="block py-2 px-4 rounded font-semibold"
          active-class="bg-teal-500/10 text-teal-400"
        >
          Dashboard
        </router-link>
      </nav>
    </aside>

    <main class="flex-1 overflow-y-auto p-8">
      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
// Import RouterLink to make it explicit, though it's often globally available.
import { RouterLink } from 'vue-router';
</script>