<template>
<NavBar />
<div class="about-section">
    <!--Page Header-->
    <div class="page-header">
      <h1 class="page-title">About Ithaca Insights</h1>
      <p class="page-subtitle">Making Ithaca's Chaotic Rental Market Clear As Cayuga</p>
    </div>

    <!--Mission Section-->
    <section class="mission-section">
      <div class="mission-container">
        <h2 class="section-title">Our Mission</h2>
        <p class="mission-text">
          Ithaca Insights was born from a simple observation: the rental market in Ithaca is a total fiasco. 
          How can we, as college students, make sure that we are getting a great deal and we aren't getting ripped off? 
          <br />
          <br />
          Our platform bridges this gap by providing data-driven insights into rental pricing, neighborhood characteristics, 
          and housing accessibility across Tompkins County.
        </p>
      </div>
    </section>

    <!--Team Section-->
    <section class="team-section">
      <div class="team-container">
        <h2 class="section-title">Meet the Team</h2>
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
      </div>
    </section>

    <!--Partners Section-->
    <section class="partners-section">
      <div class="partners-container">
        <h2 class="section-title">Our Partners</h2>
        <p class="partners-intro">
          We're grateful for the support and collaboration of these organizations that help make Ithaca Insights possible.
        </p>
        <div class="partners-grid">
          <div
            class="partner-card"
            v-for="(partner, index) in partners"
            :key="index"
          >
            <img
              class="partner-logo"
              :src="partner.logo"
              :alt="`${partner.name} logo`"
            />
            <h3 class="partner-name">{{ partner.name }}</h3>
            <p class="partner-description">{{ partner.description }}</p>
            <a :href="partner.website" target="_blank" class="partner-link" v-if="partner.website">
              Visit Website
            </a>
          </div>
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
import cdjLogo from '@/assets/CDJLogo.png';
import armadaLogo from '@/assets/armadalogo.png';
import maitrixLogo from '@/assets/MaitrixLabsLogo.png';

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

const partners = [
  {
    name: 'Cornell Data Journal',
    description: 'Organization spearheading data-driven journalism on the Hill',
    logo: cdjLogo,
    website: 'https://cornelldatajournal.org/'
  },
  {
    name: 'Cornell Armada',
    description: 'If it ships from Cornell, it probably started here',
    logo: armadaLogo,
    website: 'https://armada.build/'
  },
  {
    name: 'Maitrix Labs',
    description: 'Some college kids building next-gen AI/ML products for the CRE industry',
    logo: maitrixLogo,
    website: 'https://www.linkedin.com/company/maitrix-labs/about'
  }
];

</script>

<style scoped>
/* Layout */
.about-section {
  margin-top: 2%;
  width: 100vw;
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center; 
  gap: 60px;
  padding-bottom: 4rem;
}

/* Page Header */
.page-header {
  text-align: center;
  padding: 4rem 2rem 2rem;
  background: #061559;
  color: white;
  width: 100%;
}

.page-title {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 1rem;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.3);
}

.page-subtitle {
  font-size: 1.25rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* Section Styling */
.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1e3a8a;
  margin-bottom: 2rem;
  text-align: center;
}

/* Mission Section */
.mission-section {
  padding: 0 2rem;
  max-width: 60%;
  text-align: center;
}

.mission-container {
  margin: 0 auto;
}

.mission-text {
  font-size: 1.3rem;
  color: #4b5563;
  line-height: 1.8;
  margin-bottom: 1.5rem;
}

/* Team Section */
.team-section { 
  padding: 2rem 5vw;
  align-items: center;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.team-container {
  max-width: 1200px;
  width: 100%;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  justify-items: center;
}

.team-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
  width: 100%;
  max-width: 280px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.team-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.avatar-face {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  background: #e0e7ff;
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
  margin-bottom: 0.5rem;
}

.member-role {
  font-size: 1rem;
  color: #4b5563;
}

/* Partners Section */
.partners-section {
  padding: 2rem 5vw;
  align-items: center;
  display: flex;
  flex-direction: column;
  width: 100%;
  background: #f8fafc;
}

.partners-container {
  max-width: 1200px;
  width: 100%;
  text-align: center;
}

.partners-intro {
  font-size: 1.1rem;
  color: #4b5563;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.partners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  justify-items: center;
}

.partner-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
  width: 100%;
  max-width: 350px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.partner-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.partner-logo {
  width: 80px;
  height: 80px;
  object-fit: contain;
  margin: 0 auto 1rem;
  background: #f8fafc;
  border-radius: 8px;
  padding: 1rem;
}

.partner-name {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 1rem;
}

.partner-description {
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.partner-link {
  display: inline-block;
  padding: 8px 16px;
  background: #1e3a8a;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.3s ease;
}

.partner-link:hover {
  background: #1d4ed8;
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
  .page-title {
    font-size: 2rem;
  }

  .page-subtitle {
    font-size: 1rem;
    padding: 0 1rem;
  }

  .section-title {
    font-size: 1.8rem;
  }

  .mission-text {
    font-size: 1rem;
    padding: 0 1rem;
  }

  .team-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .team-card {
    padding: 1.5rem;
  }

  .avatar-face {
    width: 100px;
    height: 100px;
  }

  .partners-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }

  .partner-card {
    padding: 1.5rem;
  }

  .about-section {
    gap: 40px;
  }
}

</style>
