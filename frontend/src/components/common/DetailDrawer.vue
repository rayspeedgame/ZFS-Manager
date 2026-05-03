<script setup>
const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
  modelValue: { type: Boolean, required: true },
});

const emit = defineEmits(["update:modelValue"]);

function close() {
  emit("update:modelValue", false);
}
</script>

<template>
  <div v-if="props.modelValue" class="drawer-backdrop" @click.self="close">
    <aside class="detail-drawer">
      <div class="drawer-header">
        <div>
          <h3>{{ title }}</h3>
          <p>{{ description }}</p>
        </div>
        <button type="button" class="drawer-close" @click="close">Close</button>
      </div>
      <div class="drawer-body">
        <slot />
      </div>
    </aside>
  </div>
</template>
