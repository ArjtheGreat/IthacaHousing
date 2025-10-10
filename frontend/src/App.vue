<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useHead } from '@vueuse/head';

useHead({
  title: 'Ithaca Insights | Maitrix Labs',
  meta: [
    { property: 'og:title', content: 'Ithaca Insights | Maitrix Labs' },
    { property: 'og:description', content: 'All the key info and history you need tok now about Ithaca and Cornell.' },
    { property: 'og:image', content: 'https://ithacainsights.com/favicon.ico' },
    { property: 'og:url', content: 'https://ithacainsights.com/' },
    { property: 'og:type', content: 'website' }
  ]
});
</script>

<template>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <router-view />
</template>


<style>
body {
  background-color:  #f5f7fa;
}
body {
  margin: 0;
  padding: 0 !important;
  overflow-x: hidden;
}

/* header {
  line-height: 1.5;
  max-height: 100vh;
}
 
.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
} */
</style>
