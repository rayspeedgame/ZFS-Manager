<script setup>
import { useI18n } from "vue-i18n";

const props = defineProps({
  fields: { type: Array, required: true },
  modelValue: { type: Object, default: () => ({}) },
  readonly: { type: Boolean, default: false },
  getInputSpec: { type: Function, default: null },
  metaByField: { type: Object, default: () => ({}) },
  defaultOptionLabel: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
  gridClass: { type: String, default: "detail-grid" },
  itemClass: { type: String, default: "" },
});

const { t, te } = useI18n();
const emit = defineEmits(["update:modelValue"]);

function fieldName(field) {
  return typeof field === "string" ? field : field.name;
}

function fieldLabel(field) {
  if (typeof field === "string") {
    return te(`properties.names.${field}`) ? t(`properties.names.${field}`) : field;
  }
  if (field.labelKey && te(field.labelKey)) {
    return t(field.labelKey);
  }
  if (field.label) {
    return field.label;
  }
  return te(`properties.names.${field.name}`) ? t(`properties.names.${field.name}`) : field.name;
}

function inputSpec(name) {
  return props.getInputSpec ? props.getInputSpec(name) || { type: "text" } : { type: "text" };
}

function optionLabel(option) {
  if (option?.labelKey && te(option.labelKey)) {
    return t(option.labelKey);
  }
  return option?.label ?? option?.value ?? "";
}

function placeholderText(name) {
  const spec = inputSpec(name);
  if (spec.placeholderKey && te(spec.placeholderKey)) {
    return t(spec.placeholderKey);
  }
  return spec.placeholder || "";
}

function updateValue(name, value) {
  // Emit a full draft object so container views can keep a single source of truth.
  emit("update:modelValue", {
    ...(props.modelValue || {}),
    [name]: value,
  });
}
</script>

<template>
  <dl :class="gridClass">
    <div
      v-for="field in fields"
      :key="fieldName(field)"
      :class="itemClass"
    >
      <dt>{{ fieldLabel(field) }}</dt>
      <dd>
        <template v-if="readonly">
          <span>{{ metaByField[fieldName(field)]?.value ?? "-" }}</span>
          <span v-if="metaByField[fieldName(field)]?.source" class="subtle-text">
            ({{ metaByField[fieldName(field)].source }})
          </span>
        </template>

        <template v-else>
          <select
            v-if="inputSpec(fieldName(field)).type === 'select'"
            :value="modelValue[fieldName(field)]"
            class="property-field"
            :disabled="disabled"
            @change="updateValue(fieldName(field), $event.target.value)"
          >
            <option v-if="defaultOptionLabel" value="">{{ defaultOptionLabel }}</option>
            <option
              v-for="option in inputSpec(fieldName(field)).options || []"
              :key="fieldName(field) + ':' + option.value"
              :value="option.value"
            >
              {{ optionLabel(option) }}
            </option>
          </select>

          <input
            v-else
            :value="modelValue[fieldName(field)]"
            type="text"
            class="property-field"
            :placeholder="placeholderText(fieldName(field))"
            :disabled="disabled"
            @input="updateValue(fieldName(field), $event.target.value)"
          />

          <span v-if="metaByField[fieldName(field)]" class="property-meta">
            <template v-if="metaByField[fieldName(field)].prefix">
              {{ metaByField[fieldName(field)].prefix }}
            </template>
            {{ metaByField[fieldName(field)].value }}
            <span v-if="metaByField[fieldName(field)].source" class="subtle-text">
              ({{ metaByField[fieldName(field)].source }})
            </span>
          </span>
        </template>
      </dd>
    </div>
  </dl>
</template>
