import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import type { Session } from '@supabase/supabase-js';
import { supabase } from '@/services/supabase';

/** The signed-in Supabase user, shared across the app */
export const useAuthStore = defineStore('auth', () => {
  const session = ref<Session | null>(null);
  const ready = ref(false);
  const configured = !!supabase;

  // No Supabase keys: skip sign-in and use one shared local account.
  const user = computed(() => {
    if (!configured) return { id: 'local', email: null as string | null };
    const u = session.value?.user;
    return u ? { id: u.id, email: u.email ?? null } : null;
  });
  const email = computed(() => user.value?.email ?? null);

  let started = false;
  async function init() {
    if (started) return;
    started = true;
    if (!supabase) {
      ready.value = true;
      return;
    }
    // Also picks up the session from a magic-link redirect
    const { data } = await supabase.auth.getSession();
    session.value = data.session;
    ready.value = true;
    supabase.auth.onAuthStateChange((_event, s) => {
      session.value = s;
    });
  }

  /** Emails a sign-in link that brings them back to the page they're on */
  async function sendMagicLink(address: string) {
    if (!supabase) throw new Error("Sign-in isn't configured yet.");
    const { error } = await supabase.auth.signInWithOtp({
      email: address,
      options: { emailRedirectTo: window.location.origin + window.location.pathname },
    });
    if (error) throw new Error(error.message);
  }

  async function signOut() {
    await supabase?.auth.signOut();
    session.value = null;
  }

  /** A fresh access token for backend calls (supabase-js refreshes it when needed) */
  async function accessToken(): Promise<string | null> {
    if (!supabase) return null;
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }

  return { session, ready, configured, user, email, init, sendMagicLink, signOut, accessToken };
});
