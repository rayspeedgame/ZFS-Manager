<script setup>
import { ref, nextTick, onBeforeUnmount } from "vue";

const props = defineProps({
  text: { type: String, required: true },
  width: { type: String, default: "260px" },
});

const iconRef = ref(null);
const visible = ref(false);
const popupStyle = ref({});

let hideTimer = null;

function show() {
  clearTimeout(hideTimer);
  visible.value = true;
  nextTick(positionPopup);
}

function hide() {
  hideTimer = setTimeout(() => {
    visible.value = false;
  }, 100);
}

function positionPopup() {
  if (!iconRef.value) return;
  const iconRect = iconRef.value.getBoundingClientRect();
  const popupWidth = parseInt(props.width, 10) || 260;
  const gap = 8;
  const vw = window.innerWidth;
  const vh = window.innerHeight;

  // Bottom-anchored: tooltip sits entirely above the icon, never overlaps it
  const bottom = `${vh - iconRect.top + gap}px`;

  // Horizontal: center under icon, clamp to viewport
  let left = iconRect.left + iconRect.width / 2 - popupWidth / 2;
  if (left < gap) left = gap;
  if (left + popupWidth > vw - gap) {
    left = vw - popupWidth - gap;
  }

  // Check if there's enough room above
  const iconTopGap = iconRect.top;
  const estimatedHeight = 200; // average help text height, re-checked after paint
  let finalBottom = bottom;
  let finalTop = "auto";
  let finalLeft = `${left}px`;

  if (iconTopGap < gap + estimatedHeight && iconRect.bottom + gap + estimatedHeight < vh - gap) {
    // Not enough above → show below the icon
    finalBottom = "auto";
    finalTop = `${iconRect.bottom + gap}px`;
  }

  popupStyle.value = {
    width: props.width,
    left: finalLeft,
    top: finalTop,
    bottom: finalBottom,
  };
}

onBeforeUnmount(() => {
  clearTimeout(hideTimer);
});
</script>

<template>
  <span
    class="help-tooltip-wrapper"
    @mouseenter="show()"
    @mouseleave="hide()"
  >
    <span
      ref="iconRef"
      class="help-tooltip-icon"
      tabindex="0"
      role="button"
      :aria-label="text"
    >?</span>
    <Transition name="tooltip-fade">
      <div
        v-if="visible"
        class="help-tooltip-popup"
        :style="popupStyle"
      >
        <slot>
          <p>{{ text }}</p>
        </slot>
      </div>
    </Transition>
  </span>
</template>

<style scoped>
.help-tooltip-wrapper {
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
  cursor: help;
}

.help-tooltip-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 4px;
  border-radius: 50%;
  background: var(--surface-3, #e0e0e0);
  color: var(--text-2, #666);
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
  user-select: none;
  transition: background 0.15s, color 0.15s;
}

.help-tooltip-icon:hover {
  background: var(--accent, #4a90d9);
  color: #fff;
}

.help-tooltip-popup {
  position: fixed;
  z-index: 999999;
  padding: 10px 14px;
  border-radius: 6px;
  background: var(--surface-1, #1e1e1e);
  color: var(--text-1, #e0e0e0);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-line;
  word-break: break-word;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  pointer-events: none;
  text-align: left;
}

.help-tooltip-popup p {
  margin: 0;
}

.tooltip-fade-enter-active,
.tooltip-fade-leave-active {
  transition: opacity 0.15s ease;
}

.tooltip-fade-enter-from,
.tooltip-fade-leave-to {
  opacity: 0;
}
</style>