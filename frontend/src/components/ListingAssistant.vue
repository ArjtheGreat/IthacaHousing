<template>
  <div class="assistant-root">
    <!-- Launcher -->
    <button v-if="!open" class="assistant-launcher" @click="open = true" aria-label="Open listing assistant">
      <i class="fa-solid fa-wand-magic-sparkles"></i>
      <span>Ask AI</span>
    </button>

    <!-- Panel -->
    <div v-else class="assistant-panel" role="dialog" aria-label="Listing assistant">
      <div class="assistant-head">
        <div>
          <div class="assistant-title">Find me a place</div>
          <div class="assistant-sub">Describe what you want; I'll set the filters and pick listings.</div>
        </div>
        <div class="assistant-head-actions">
          <button v-if="turns.length" class="assistant-icon-btn" @click="clearChat" title="New search">
            <i class="fa-solid fa-rotate-left"></i>
          </button>
          <button class="assistant-icon-btn" @click="open = false" title="Minimize">
            <i class="fa-solid fa-minus"></i>
          </button>
        </div>
      </div>

      <div ref="scroller" class="assistant-body">
        <div v-if="!turns.length" class="assistant-empty">
          <p>Try:</p>
          <button v-for="ex in examples" :key="ex" class="assistant-example" @click="send(ex)">{{ ex }}</button>
        </div>

        <template v-for="(turn, i) in turns" :key="i">
          <div v-if="turn.role === 'user'" class="msg msg-user">{{ turn.content }}</div>
          <div v-else class="msg msg-assistant">
            <p>{{ turn.content }}</p>
            <div v-if="turn.filterSummary" class="filter-chip">
              <i class="fa-solid fa-filter"></i> {{ turn.filterSummary }}
            </div>
            <ol v-if="turn.recommendations?.length" class="recs">
              <li
                v-for="(rec, n) in turn.recommendations"
                :key="rec.listingid"
                class="rec"
                :class="{ active: rec.listingid === selectedId }"
                @click="select(rec.listingid)"
              >
                <span class="rec-num">{{ n + 1 }}</span>
                <div class="rec-main">
                  <div class="rec-top">
                    <span class="rec-addr">{{ rec.address || 'Listing' }}</span>
                    <span class="rec-rent">{{ formatRent(rec.rent_per_person) }}<small>/person</small></span>
                  </div>
                  <div class="rec-meta">{{ bedBath(rec) }}</div>
                  <div class="rec-reason">{{ rec.reason }}</div>
                </div>
              </li>
            </ol>
          </div>
        </template>

        <div v-if="loading" class="msg msg-assistant msg-loading">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
        <div v-if="error" class="msg msg-error">{{ error }}</div>
      </div>

      <form class="assistant-input" @submit.prevent="send()">
        <textarea
          v-model="draft"
          rows="2"
          maxlength="500"
          placeholder="e.g. 2 bed under $1,200, walk to the Arts Quad, pets OK"
          :disabled="loading"
          @keydown.enter.exact.prevent="send()"
        ></textarea>
        <button type="submit" :disabled="loading || !draft.trim()" aria-label="Send">
          <i class="fa-solid fa-paper-plane"></i>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue';
import {
  fetchAssistantRecommendations,
  type AssistantResponse,
  type AssistantRecommendation,
  type AssistantFilters,
} from '@/services/fetch';

const props = defineProps<{
  /** Filters currently set in the Personal Preferences panel */
  currentFilters: Record<string, string | number | null>;
  /** Listing the map currently has open, so the matching card shows as active */
  selectedId?: string | null;
}>();

const emit = defineEmits<{
  /** A new answer: apply its filters and highlight its picks */
  (e: 'result', value: AssistantResponse): void;
  /** User clicked a recommendation card */
  (e: 'select', listingid: string): void;
  /** User started over: remove the highlights */
  (e: 'clear'): void;
}>();

interface Turn {
  role: 'user' | 'assistant';
  content: string;
  recommendations?: AssistantRecommendation[];
  filterSummary?: string;
}

const examples = [
  '2 bedroom under $1,200 per person, walkable to the Arts Quad',
  'Cheap studio or 1 bed, bike to Eng Quad in under 15 min',
  'Big house for 5 friends, good value, near Collegetown',
];

const open = ref(false);
const draft = ref('');
const turns = ref<Turn[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);
const scroller = ref<HTMLElement | null>(null);

const DEST_LABELS: Record<string, string> = { agriculturequad: 'Ag Quad', artsquad: 'Arts Quad', engineeringquad: 'Eng Quad' };
const MODE_LABELS: Record<string, string> = { walk: 'walk', bike: 'bike', drive: 'drive' };

const formatRent = (n: number | null) => (n && n > 0 ? `$${Math.round(n).toLocaleString('en-US')}` : '—');

function bedBath(rec: AssistantRecommendation) {
  const beds = rec.beds === 0 ? 'Studio' : rec.beds != null ? `${rec.beds} bd` : null;
  const baths = rec.baths != null ? `${rec.baths} ba` : null;
  return [beds, baths].filter(Boolean).join(' · ');
}

function summarize(f: AssistantFilters | null) {
  if (!f) return '';
  const parts: string[] = [];
  if (f.beds) parts.push(`${f.beds}${f.beds >= 5 ? '+' : ''} bed`);
  if (f.baths) parts.push(`${f.baths}${f.baths >= 3 ? '+' : ''} bath`);
  if (f.budget) parts.push(`≤ $${f.budget.toLocaleString('en-US')}/person`);
  if (f.commute) parts.push(`< ${f.commute.max_time} min ${MODE_LABELS[f.commute.mode]} to ${DEST_LABELS[f.commute.destination]}`);
  return parts.length ? parts.join(' · ') : 'Filters cleared';
}

async function scrollToEnd() {
  await nextTick();
  scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' });
}

async function send(text?: string) {
  const content = (text ?? draft.value).trim();
  if (!content || loading.value) return;
  draft.value = '';
  error.value = null;
  turns.value.push({ role: 'user', content });
  loading.value = true;
  scrollToEnd();

  try {
    // Send the conversation as plain text turns (recommendations ride along in the assistant text)
    const history = turns.value.map(t => ({
      role: t.role,
      content: t.role === 'assistant' && t.recommendations?.length
        ? `${t.content}\nRecommended: ${t.recommendations.map(r => `${r.listingid} (${r.address})`).join('; ')}`
        : t.content,
    }));
    const res = await fetchAssistantRecommendations(history, props.currentFilters);
    turns.value.push({
      role: 'assistant',
      content: res.reply,
      recommendations: res.recommendations,
      filterSummary: summarize(res.filters),
    });
    emit('result', res);
  } catch (e) {
    turns.value.pop(); // let them edit and resend
    draft.value = content;
    error.value = e instanceof Error ? e.message : 'Something went wrong.';
  } finally {
    loading.value = false;
    scrollToEnd();
  }
}

function select(id: string) {
  emit('select', id);
}

function clearChat() {
  turns.value = [];
  error.value = null;
  emit('clear');
}
</script>

<style scoped>
.assistant-root {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1001; /* above the map and legend, below the listing sidebar's mobile sheet */
  font-family: 'Inter', sans-serif;
}

.assistant-launcher {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border: none;
  border-radius: 999px;
  background: #355C7D;
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: transform 0.15s ease, background 0.15s ease;
}
.assistant-launcher:hover { background: #2a4a66; transform: translateY(-1px); }

.assistant-panel {
  width: 380px;
  max-width: calc(100vw - 32px);
  height: min(560px, calc(100vh - 120px));
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.assistant-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 14px;
  background: #355C7D;
  color: #fff;
}
.assistant-title { font-weight: 700; font-size: 1rem; }
.assistant-sub { font-size: 0.75rem; opacity: 0.85; margin-top: 2px; }
.assistant-head-actions { display: flex; gap: 4px; }
.assistant-icon-btn {
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: #fff;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  cursor: pointer;
}
.assistant-icon-btn:hover { background: rgba(255, 255, 255, 0.3); }

.assistant-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #f8fafc;
}

.assistant-empty p { font-size: 0.8rem; color: #6b7280; margin: 0 0 6px; }
.assistant-example {
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 6px;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  font-size: 0.82rem;
  color: #374151;
  cursor: pointer;
}
.assistant-example:hover { border-color: #355C7D; color: #355C7D; }

.msg { font-size: 0.86rem; line-height: 1.4; border-radius: 10px; padding: 8px 11px; max-width: 92%; }
.msg p { margin: 0; }
.msg-user { align-self: flex-end; background: #355C7D; color: #fff; white-space: pre-wrap; }
.msg-assistant { align-self: flex-start; background: #fff; border: 1px solid #e5e7eb; color: #1f2937; }
.msg-error { align-self: stretch; background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }

.filter-chip {
  margin-top: 8px;
  display: inline-block;
  font-size: 0.75rem;
  background: #eff6ff;
  color: #1e3a8a;
  padding: 3px 8px;
  border-radius: 999px;
}

.recs { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.rec {
  display: flex;
  gap: 8px;
  padding: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.rec:hover, .rec.active { border-color: #f59e0b; background: #fffbeb; }
.rec-num {
  flex: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f59e0b;
  color: #fff;
  font-weight: 700;
  font-size: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}
.rec-main { min-width: 0; flex: 1; }
.rec-top { display: flex; justify-content: space-between; gap: 6px; }
.rec-addr { font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rec-rent { font-weight: 700; white-space: nowrap; }
.rec-rent small { font-weight: 400; color: #6b7280; }
.rec-meta { font-size: 0.75rem; color: #6b7280; }
.rec-reason { font-size: 0.8rem; color: #374151; margin-top: 3px; }

.msg-loading { display: flex; gap: 4px; padding: 12px; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #9ca3af; animation: blink 1.2s infinite ease-in-out; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%, 80%, 100% { opacity: 0.3; } 40% { opacity: 1; } }

.assistant-input { display: flex; gap: 8px; padding: 10px; border-top: 1px solid #e5e7eb; background: #fff; }
.assistant-input textarea {
  flex: 1;
  resize: none;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  font: inherit;
  font-size: 0.86rem;
}
.assistant-input textarea:focus { outline: 2px solid #355C7D; outline-offset: -1px; }
.assistant-input button {
  width: 40px;
  border: none;
  border-radius: 8px;
  background: #355C7D;
  color: #fff;
  cursor: pointer;
}
.assistant-input button:disabled { opacity: 0.4; cursor: default; }

@media (max-width: 768px) {
  .assistant-root { right: 12px; bottom: 12px; }
  .assistant-panel { height: min(520px, calc(100vh - 100px)); }
}
</style>
