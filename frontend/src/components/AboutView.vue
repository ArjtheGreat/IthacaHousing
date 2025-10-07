<template>
<NavBar />
<div class="info-section">
    <!--Hero Section MAKE BALANCE SMOOTHER MAKE WORDS ON EACH LINE EQUAL-->
    <div class="hero">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <h1 class="hero-title">Explore Fair Rent in Ithaca</h1>
        <p class="hero-subtitle">Ithaca Insights is a live dashboard uncovering rental pricing inefficiencies across Tompkins County.</p>
        <button class="cta-button"><router-link to="/rent">View Map</router-link></button>
      </div>
    </div>


    <!--Value Prop Section-->
    <section class="value-prop-section">
      <div class="value-prop-container">
        <h2 class="value-prop-heading">Why Ithaca Insights?</h2>
        <div class="value-prop-cards">

          <div class="value-card">
            <h3 class="value-title">Transparent Pricing</h3>
            <p class="value-text">
              We reveal the true price of listings by comparing market rent to actual listing data—empowering renters and informing city planners. 
            </p>
          </div>

          <div class="value-card">
            <h3 class="value-title">Data-Driven Insights</h3>
            <p class="value-text">
            We incorporate real-time data from Tompkins County into regression models and geospatial analysis tools that turn raw data into actionable intelligence.
            </p>
          </div>

          <div class="value-card">
            <h3 class="value-title">Accessible for All</h3>
            <p class="value-text">
              Built for students, landlords, and policymakers alike. Our interface is intuitive, fast, and freely available to the public.
            </p>
          </div>

        </div>
      </div>
    </section>

    <!--Team Section-->
    <section class="team-section">
      <h2 class="team-title">Meet the Team</h2>
      <div class="team-grid">
        <div
          class="team-card"
          v-for="(member, index) in teamMembers"
          :key="index"
        >
          <img
            class="avatar-face"
            :src="member.avatar"
            :alt="`${member.name}'s avatar`"
          />
          <h3 class="member-name">{{ member.name }}</h3>
          <p class="member-role">{{ member.role }}</p>
        </div>
      </div>
    </section>
</div>
</template>
  
  
<script setup lang="ts">
import NavBar from "@/components/NavBar.vue";
import arjunImg from '@/assets/avatars/arjunmaitra.jpeg';
import stevenImg from '@/assets/avatars/stevenzhou.jpeg';
import ethanImg from '@/assets/avatars/ethanyang.jpeg';
import vivianImg from '@/assets/avatars/vivianguo.jpeg';

const teamMembers = [
  {
    name: 'Arjun Maitra',
    role: 'Head of Data Science',
    avatar: arjunImg
  },
  {
    name: 'Steven Zhou',
    role: 'Data Scientist Emeritus',
    avatar: stevenImg
  },
  {
    name: 'Ethan Yang',
    role: 'Head of Marketing',
    avatar: ethanImg
  },
  {
    name: 'Vivian Guo',
    role: 'Data Analyst',
    avatar: vivianImg
  }
];

</script>

<style scoped>
/* Layout */
.info-section {
  margin-top: 2%;
  width: 100vw;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center; 
  gap: 20px;
  

}


/* Hero Section */
.hero {
  position: relative;
  padding: 3rem 0;
  text-align: center;
  margin-top: 2%;
  width: 100%;
  background-image: url('@/assets/ithaca.jpg');
  background-size: cover;
  background-position: center;
  overflow: hidden;
  border-bottom: 1px solid black;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none; /* Let clicks through */
  z-index: 1;
  backdrop-filter: blur(4px);
  background: linear-gradient(
    to right,
    rgba(0, 0, 0, 0) 0%,
    rgba(0, 0, 0, 0.6) 25%,
    rgba(0, 0, 0, 0.75) 50%,
    rgba(0, 0, 0, 0.6) 75%,
    rgba(0, 0, 0, 0) 100%
  );
  
}

.hero-content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: white;
}

.hero-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hero-title {
  font-size: 3rem;
  font-weight: 700;
  color: #ffffff; /* pure white for max contrast */
  white-space: nowrap;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.6); /* adds subtle shadow for readability */
}

.hero-subtitle {
  font-size: 1.25rem;
  color: #f0f0f0;
  line-height: 1.6;
  max-width: 600px;
  text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
}

.cta-button {
  display: inline-block;
  padding: 12px 28px;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
  background: #1e3a8a;
  transition: all 0.3s ease;
  border: none;             
  box-shadow: none;           
  appearance: none;          
  border-radius: 6px;         
}

.cta-button a {
  color: white;
}

.cta-button:hover {
  transform: scale(1.05);
  background: #1d4ed8;
}

/* Value Prop Section */
.value-prop-section {
  padding: 20px 20px;
  font-family: 'DM Sans', sans-serif;
}

.value-prop-container {
  max-width: 1100px;
  margin: 0 auto;
}

.value-prop-heading {
  font-size: 2.75rem;
  font-weight: 700;
  color: #1e3a8a;
  margin-bottom: 3rem;
  text-align: center;

}

.value-prop-cards {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 30px;
}

.value-card {
  background: #ffffff;
  padding: 30px 25px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  /* box-shadow: 0 10px 24px rgba(0, 0, 0, 0.06); */
  width: 300px;
  transition: transform 0.3s ease;
}

.value-card:hover {
  transform: translateY(-6px);
}

.value-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 1rem;
  text-align: left;
}

.value-text {
  font-size: 1.1rem;
  color: #4b5563;
  line-height: 1.6;
}


/* Team Section */
.team-section { 
  padding: 2rem 5vw 4rem;
  align-items: center;
  display: flex;
  flex-direction: column;
}

.team-title {
  font-size: 2rem;
  color: #1e3a8a;
  font-weight: 700;
  margin-bottom: 2rem;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr); /* exactly 4 equal columns */
  gap: 2rem;
}

.team-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: left;
}

.avatar-face {
  width: 100%;
  aspect-ratio: 1/1;         /* Ensures it's a perfect square */
  background: #e0e7ff;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.avatar-face img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}


.member-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 0.25rem;
}

.member-role {
  font-size: 1rem;
  color: #4b5563;
}

/* Animation */
@keyframes fadeIn {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .hero-title {
    margin-top: 20px;
    font-size: 1.8rem;
    white-space: normal;
    padding: 0 1rem;
  }

  .hero-subtitle {
    font-size: 1rem;
    padding: 0 1.5rem;
    max-width: 90%;
    text-align: center;
  }

  .cta-button {
    font-size: 1rem;
    padding: 10px 20px;
  }

  .value-prop-heading {
    font-size: 1.8rem;
    margin-bottom: 2rem;
    padding: 0 1rem;
  }

  .value-prop-cards {
    flex-direction: column;
    align-items: center;
  }

  .value-card {
    width: 90%;
    padding: 20px;
  }

  .value-title {
    font-size: 1.3rem;
    text-align: center;
  }

  .value-text {
    font-size: 1rem;
    text-align: center;
  }

  .team-title {
    font-size: 1.5rem;
    text-align: center;
  }

  .team-grid {
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .team-card {
    padding: 1rem;
    text-align: center;
  }

  .avatar-face {
    width: 100%;
    max-width: 120px;
    margin: 0 auto 1rem;
  }

  .member-name {
    font-size: 1rem;
  }

  .member-role {
    font-size: 0.9rem;
  }

  .info-section {
    gap: 12px;
  }
}

</style>
  