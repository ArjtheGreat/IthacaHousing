<template>
<nav class="navbar-container">
    <div class="navbar-inner">
        <!-- Logo and Brand (Aligned to the far left) -->
        <div class="navbar-brand">
            <img src="@/assets/CDJLogo.png" alt="Logo" class="navbar-logo" />
            <div class="navbar-title">
            <router-link to="/" class="navbar-name">Ithaca Insights</router-link>
            <span class="navbar-subtitle">by Cornell Data Journal</span>
            </div>
        </div>

         <!-- Hamburger Icon (Mobile only) -->
        <div class="hamburger" @click="toggleMenu">
            <div class="bar" />
            <div class="bar" />
            <div class="bar" />
        </div>

        <!-- Navigation Menu -->
        <ul class="navbar-menu" :class="{ 'menu-open': menuOpen }">
            <li><router-link to="/" active-class="active-link">Home</router-link></li>
            <li><router-link to="/rent" active-class="active-link">Rental Valuation</router-link></li>
            <li><router-link to="/inside-ithaca" active-class="active-link">Inside Ithaca</router-link></li>
            <!-- <li><router-link to="/history" active-class="active-link">Time Capsule</router-link></li>
            <li><router-link to="/urbangrowth" active-class="active-link">Zoning & Site Selection</router-link></li> -->
            <!-- <li><a href="https://cornelldatajournal.org/" target="_blank" active-class="active-link">Cornell Data Journal</a></li> -->
        </ul>
    </div>
</nav>
</template>

<script setup lang="ts">
import { ref } from 'vue';
const menuOpen = ref(false);
const toggleMenu = () => (menuOpen.value = !menuOpen.value);
</script>


<style scoped>
/* Navbar Container */
.navbar-container {
    background: rgba(255, 255, 255, 0.9);  /* Translucent white */
    backdrop-filter: blur(12px);            /* Frosted glass effect */
    -webkit-backdrop-filter: blur(12px);    /* For Safari support */
    /* box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1); */
    border-bottom: 2px solid rgba(0, 0, 0, 0.2);
    padding: 8px 20px;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 100;
}

/* Inner Flex Container */
.navbar-inner {
    display: flex;
    align-items: center;
    max-width: 100%;
    margin: 0 auto;
}

.navbar-brand {
    display: flex;
    align-items: center; 
    gap: 0px; 
}

/* Logo */
.navbar-logo {
    width: 40px;
    height: auto;
}

/* Title and Subtitle Container */
.navbar-title {
    display: flex;
    flex-direction: column; 
    gap: 0px;
    line-height: 1.2; 
}

.navbar-title a:hover {
    background: none !important;
    color: initial !important;
}

/* Main Title */
.navbar-name {
    font-size: 1.1rem;
    font-weight: bold;
    color: #151366;
    text-decoration: none;
    transition: color 0.2s ease-in-out;
}

/* Subtitle */
.navbar-subtitle {
    font-size: 0.9rem;
    color: #666;
    font-weight: normal;
}


/* Menu Links */
.navbar-menu {
    display: flex;
    gap: 8px;
    list-style: none;
}

.navbar-menu li {
    font-size: 0.95rem;
}

.navbar-menu a {
    text-decoration: none;
    color: #374151;
    transition: color 0.2s ease-in-out;
    padding: 4px 12px;
    display: inline-block;
    border-bottom: 2px solid transparent;
    border-radius: 4px;
}

.navbar-menu a:hover {
    color: #1d4ed8;
    background-color: #1d4fd82e;
}

.active-link {
    color: #1d4ed8;
    font-weight: bold;
    border-bottom: 2px solid #1d4ed8;
}

/* Hamburger Icon (Mobile only) */
.hamburger {
  display: none;
  flex-direction: column;
  cursor: pointer;
  gap: 4px;
}

.bar {
  width: 24px;
  height: 3px;
  background-color: #374151;
  border-radius: 2px;
}


@media (max-width: 768px) {
  .navbar-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 100%;
    margin: 0 auto;

    flex-wrap: wrap;
  }

  .navbar-menu {
    display: none;
    flex-direction: column;
    width: 100%;
    padding-top: 1rem;
  }

  .navbar-menu.menu-open {
    display: flex;
  }

  .navbar-menu li {
    text-align: center;
    padding: 8px 0;
  }

  .hamburger {
    display: flex;
  }
}

</style>
  