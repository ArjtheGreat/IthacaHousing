<template>
  <div class="assistant-root">
    <!-- Launcher -->
    <button v-if="!open" class="assistant-launcher" @click="reopen" aria-label="Open listing assistant">
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
          <button
            v-if="auth.user"
            class="assistant-icon-btn"
            :class="{ on: view === 'prefs' }"
            @click="togglePrefs"
            title="Your preferences"
          >
            <i class="fa-solid fa-sliders"></i>
          </button>
          <button v-if="auth.user && view === 'chat' && turns.length" class="assistant-icon-btn" @click="clearChat" title="New search">
            <i class="fa-solid fa-rotate-left"></i>
          </button>
          <button class="assistant-icon-btn" @click="minimize" title="Minimize">
            <i class="fa-solid fa-minus"></i>
          </button>
        </div>
      </div>

      <!-- Signed out (only when Supabase sign-in is configured) -->
      <div v-if="!auth.user" class="assistant-body assistant-gate">
        <template v-if="!auth.ready">
          <p>Loading…</p>
        </template>
        <template v-else-if="linkSentTo">
          <i class="fa-solid fa-envelope-circle-check gate-icon"></i>
          <p>We sent a sign-in link to <strong>{{ linkSentTo }}</strong>. Open it on this device to start using the assistant.</p>
          <button class="gate-link" @click="linkSentTo = null">Use a different email</button>
        </template>
        <form v-else class="gate-form" @submit.prevent="sendLink">
          <i class="fa-solid fa-lock gate-icon"></i>
          <p>Sign in to use the AI assistant. Each account gets {{ dailyLimit }} requests a day.</p>
          <input v-model="email" type="email" required autocomplete="email" placeholder="you@cornell.edu" :disabled="authBusy" />
          <button type="submit" class="gate-btn" :disabled="authBusy || !email.trim()">
            {{ authBusy ? 'Sending…' : 'Email me a sign-in link' }}
          </button>
          <div v-if="authError" class="msg msg-error">{{ authError }}</div>
        </form>
      </div>

      <!-- Saved preferences -->
      <div v-else-if="view === 'prefs'" class="assistant-body">
        <div class="prefs">
          <label for="prefs-text">What are you looking for?</label>
          <p class="prefs-hint">The assistant uses this every time you ask, so you don't have to repeat yourself.</p>
          <textarea
            id="prefs-text"
            v-model="prefsDraft"
            rows="4"
            maxlength="500"
            placeholder="e.g. 3 bedrooms in Collegetown, under $1,200 each, laundry in unit, walk to the Arts Quad, I have a cat"
            :disabled="prefsBusy"
          ></textarea>
          <div class="prefs-actions">
            <button
              class="gate-btn"
              :disabled="prefsBusy || !prefsDraft.trim() || prefsDraft.trim() === account?.preferences?.text || account?.preferences_remaining === 0"
              @click="savePrefs"
            >
              {{ prefsBusy ? 'Saving…' : 'Save' }}
            </button>
            <button v-if="account?.preferences" class="gate-link" :disabled="prefsBusy" @click="clearPrefs">Clear</button>
            <span v-if="account" class="prefs-count">{{ account.preferences_remaining }} update{{ account.preferences_remaining === 1 ? '' : 's' }} left today</span>
          </div>
          <div v-if="prefsError" class="msg msg-error">{{ prefsError }}</div>
          <div v-if="account?.preferences" class="prefs-saved">
            <div class="prefs-saved-label">Saved as</div>
            <div class="prefs-chips">
              <span v-for="part in account.preferences.schematic.split(' | ')" :key="part" class="filter-chip">{{ part }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else ref="scroller" class="assistant-body">
        <div v-if="account?.preferences && !turns.length" class="prefs-banner" @click="togglePrefs">
          <i class="fa-solid fa-sliders"></i> Using your preferences: {{ account.preferences.schematic }}
        </div>
        <div v-if="!turns.length" class="assistant-empty">
          <p>Try:</p>
          <button v-for="ex in examples" :key="ex" class="assistant-example" :disabled="outOfRequests" @click="send(ex)">{{ ex }}</button>
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

      <div v-if="auth.user" class="assistant-status">
        <span v-if="account">{{ account.remaining }} of {{ account.limit }} requests left today</span>
        <span v-else>&nbsp;</span>
        <span v-if="auth.email" class="assistant-who">
          {{ auth.email }} · <button class="gate-link" @click="signOut">Sign out</button>
        </span>
      </div>

      <form v-if="auth.user && view === 'chat'" class="assistant-input" @submit.prevent="send()">
        <textarea
          v-model="draft"
          rows="2"
          maxlength="500"
          :placeholder="outOfRequests ? 'No requests left today. They reset at midnight.' : 'e.g. 2 bed under $1,200, walk to the Arts Quad, pets OK'"
          :disabled="loading || outOfRequests"
          @keydown.enter.exact.prevent="send()"
        ></textarea>
        <button type="submit" :disabled="loading || outOfRequests || !draft.trim()" aria-label="Send">
          <i class="fa-solid fa-paper-plane"></i>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue';
import { useAuthStore } from '@/stores/auth';
import {
  fetchAssistantRecommendations,
  fetchAssistantAccount,
  saveAssistantPreferences,
  deleteAssistantPreferences,
  type AssistantAccount,
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
  /** User started over, minimized, or sent a new prompt: remove the highlights */
  (e: 'clear'): void;
  /** Panel reopened: put the last answer's pins back on the map */
  (e: 'restore', recommendations: AssistantRecommendation[]): void;
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

// ---------- Sign-in, daily limit, saved preferences ----------
const auth = useAuthStore();
const dailyLimit = 3;
const view = ref<'chat' | 'prefs'>('chat');
const email = ref('');
const linkSentTo = ref<string | null>(null);
const authBusy = ref(false);
const authError = ref<string | null>(null);
const account = ref<AssistantAccount | null>(null);
const prefsDraft = ref('');
const prefsBusy = ref(false);
const prefsError = ref<string | null>(null);

const outOfRequests = computed(() => account.value?.remaining === 0);

onMounted(() => auth.init());

watch(
  () => auth.user?.id,
  id => {
    account.value = null;
    turns.value = [];
    view.value = 'chat';
    if (id) {
      linkSentTo.value = null;
      loadAccount();
    }
  },
  { immediate: true },
);

async function withToken<T>(fn: (token: string) => Promise<T>): Promise<T> {
  const token = (await auth.accessToken()) ?? '';
  if (!token && auth.configured) {
    await auth.signOut();
    throw new Error('Your sign-in expired. Sign in again.');
  }
  try {
    return await fn(token);
  } catch (e) {
    if ((e as { status?: number }).status === 401) await auth.signOut();
    throw e;
  }
}

async function loadAccount() {
  try {
    account.value = await withToken(fetchAssistantAccount);
    prefsDraft.value = account.value.preferences?.text ?? '';
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Couldn't load your account.";
  }
}

async function sendLink() {
  const address = email.value.trim();
  if (!address) return;
  authBusy.value = true;
  authError.value = null;
  try {
    await auth.sendMagicLink(address);
    linkSentTo.value = address;
  } catch (e) {
    authError.value = e instanceof Error ? e.message : "Couldn't send the link. Try again.";
  } finally {
    authBusy.value = false;
  }
}

async function signOut() {
  emit('clear');
  await auth.signOut();
}

function togglePrefs() {
  view.value = view.value === 'prefs' ? 'chat' : 'prefs';
  prefsError.value = null;
  if (view.value === 'prefs') prefsDraft.value = account.value?.preferences?.text ?? prefsDraft.value;
}

async function savePrefs() {
  const text = prefsDraft.value.trim();
  if (!text) return;
  prefsBusy.value = true;
  prefsError.value = null;
  try {
    const res = await withToken(token => saveAssistantPreferences(text, token));
    if (account.value) {
      account.value.preferences = res.preferences;
      account.value.preferences_remaining = res.preferences_remaining;
    }
  } catch (e) {
    prefsError.value = e instanceof Error ? e.message : "Couldn't save your preferences.";
  } finally {
    prefsBusy.value = false;
  }
}

async function clearPrefs() {
  prefsBusy.value = true;
  prefsError.value = null;
  try {
    await withToken(deleteAssistantPreferences);
    if (account.value) account.value.preferences = null;
    prefsDraft.value = '';
  } catch (e) {
    prefsError.value = e instanceof Error ? e.message : "Couldn't clear your preferences.";
  } finally {
    prefsBusy.value = false;
  }
}

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

function minimize() {
  open.value = false;
  emit('clear');
}

function reopen() {
  open.value = true;
  const last = turns.value[turns.value.length - 1];
  if (last?.role === 'assistant' && last.recommendations?.length) {
    emit('restore', last.recommendations);
  }
}

async function send(text?: string) {
  const content = (text ?? draft.value).trim();
  if (!content || loading.value || outOfRequests.value) return;
  draft.value = '';
  error.value = null;
  emit('clear');
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
    const res = await withToken(token => fetchAssistantRecommendations(history, props.currentFilters, token));
    if (account.value && res.remaining != null) account.value.remaining = res.remaining;
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
    if ((e as { status?: number }).status === 429 && account.value && /requests for today/.test(error.value)) {
      account.value.remaining = 0;
    }
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
.assistant-icon-btn:hover, .assistant-icon-btn.on { background: rgba(255, 255, 255, 0.3); }

.assistant-gate { align-items: center; justify-content: center; text-align: center; }
.assistant-gate p { font-size: 0.86rem; color: #374151; margin: 0; }
.gate-form { display: flex; flex-direction: column; align-items: center; gap: 10px; width: 100%; }
.gate-form input {
  width: 100%;
  padding: 9px 11px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font: inherit;
  font-size: 0.88rem;
}
.gate-form input:focus { outline: 2px solid #355C7D; outline-offset: -1px; }
.gate-icon { font-size: 1.6rem; color: #355C7D; }
.gate-btn {
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  background: #355C7D;
  color: #fff;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
}
.gate-btn:disabled { opacity: 0.45; cursor: default; }
.gate-link {
  background: none;
  border: none;
  padding: 0;
  color: #355C7D;
  font: inherit;
  text-decoration: underline;
  cursor: pointer;
}
.gate-link:disabled { opacity: 0.5; cursor: default; }

.prefs { display: flex; flex-direction: column; gap: 8px; }
.prefs label { font-weight: 600; font-size: 0.9rem; color: #1f2937; }
.prefs-hint { font-size: 0.78rem; color: #6b7280; margin: -4px 0 0; }
.prefs textarea {
  resize: vertical;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  font: inherit;
  font-size: 0.86rem;
}
.prefs textarea:focus { outline: 2px solid #355C7D; outline-offset: -1px; }
.prefs-actions { display: flex; align-items: center; gap: 12px; font-size: 0.82rem; }
.prefs-count { margin-left: auto; font-size: 0.75rem; color: #6b7280; }
.prefs-saved { margin-top: 4px; }
.prefs-saved-label { font-size: 0.75rem; color: #6b7280; margin-bottom: 4px; }
.prefs-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.prefs-chips .filter-chip { margin-top: 0; }
.prefs-banner {
  font-size: 0.75rem;
  color: #1e3a8a;
  background: #eff6ff;
  border-radius: 8px;
  padding: 6px 9px;
  cursor: pointer;
}

.assistant-status {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 10px;
  font-size: 0.72rem;
  color: #6b7280;
  border-top: 1px solid #e5e7eb;
  background: #fff;
}
.assistant-who { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.assistant-example:disabled { opacity: 0.5; cursor: default; }

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

.assistant-input { display: flex; gap: 8px; padding: 0 10px 10px; background: #fff; }
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
