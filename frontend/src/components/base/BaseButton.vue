<template>
  <button
    :class="[
      'px-4 py-2 rounded font-semibold transition',
      variantClasses[variant],
      sizeClasses[size],
    ]"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}>();

const variantClasses = {
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
  danger: 'bg-red-600 text-white hover:bg-red-700',
};

const sizeClasses = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
};
</script>