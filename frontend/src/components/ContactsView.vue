<template>
<NavBar />
<div class="contacts-section">
    <!--Page Header-->
    <div class="page-header">
      <h1 class="page-title">Contact Us</h1>
      <p class="page-subtitle">Get in touch with our team for questions, partnerships, or feedback</p>
    </div>

    <!--Contact Methods-->
    <section class="contact-methods">
      <div class="contact-container">
        <h2 class="section-title">Get in Touch</h2>
        <div class="contact-grid">
          <div class="contact-card">
            <div class="contact-icon">
              <i class="fa-solid fa-envelope"></i>
            </div>
            <h3 class="contact-title">Email Us</h3>
            <p class="contact-description">Send us an email with your questions or feedback</p>
            <a href="mailto:support@ithacainsights.com" class="contact-link">
              support@ithacainsights.com
            </a>
          </div>

          <div class="contact-card">
            <div class="contact-icon">
              <i class="fa-solid fa-github"></i>
            </div>
            <h3 class="contact-title">GitHub</h3>
            <p class="contact-description">View our open-source code and contribute to the project</p>
            <a href="https://github.com/ArjtheGreat/IthacaHousing" target="_blank" class="contact-link">
              Github
            </a>
          </div>

          <!-- <div class="contact-card">
            <div class="contact-icon">
              <i class="fa-solid fa-university"></i>
            </div>
            <h3 class="contact-title">Cornell University</h3>
            <p class="contact-description">Visit us on campus or reach out to our academic advisors</p>
            <a href="mailto:research@cornell.edu" class="contact-link">
              research@cornell.edu
            </a>
          </div> -->
        </div>
      </div>
    </section>

    <!--Team Contacts-->
    <section class="team-contacts">
      <div class="team-contacts-container">
        <h2 class="section-title">Meet Our Team</h2>
        <p class="team-contacts-intro">
          Reach out to individual team members for specific inquiries about our work.
        </p>
        <div class="team-contacts-grid">
          <div
            class="team-contact-card"
            v-for="(member, index) in teamMembers"
            :key="index"
          >
            <img
              class="team-avatar"
              :src="member.avatar"
              :alt="`${member.name}'s avatar`"
            />
            <h3 class="team-member-name">{{ member.name }}</h3>
            <p class="team-member-role">{{ member.role }}</p>
            <div class="team-contact-links">
              <a :href="`mailto:${member.email}`" class="team-contact-link">
                <i class="fa-solid fa-envelope"></i>
                Email
              </a>
              <a :href="member.linkedin" target="_blank" class="team-contact-link" v-if="member.linkedin">
                <i class="fa-brands fa-linkedin"></i>
                LinkedIn
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!--Feedback Form-->
    <section class="feedback-section">
      <div class="feedback-container">
        <h2 class="section-title">Send Us Feedback</h2>
        <p class="feedback-intro">
          Help us improve Ithaca Insights by sharing your thoughts, suggestions, or reporting issues.
        </p>
        <form class="feedback-form" @submit.prevent="submitFeedback">
          <div class="form-group">
            <label for="name" class="form-label">Name (Optional)</label>
            <input 
              type="text" 
              id="name" 
              v-model="feedback.name"
              class="form-input"
              placeholder="Your name"
            />
          </div>
          
          <div class="form-group">
            <label for="email" class="form-label">Email (Optional)</label>
            <input 
              type="email" 
              id="email" 
              v-model="feedback.email"
              class="form-input"
              placeholder="your.email@example.com"
            />
          </div>
          
          <div class="form-group">
            <label for="subject" class="form-label">Subject</label>
            <select id="subject" v-model="feedback.subject" class="form-select" required>
              <option value="">Select a topic</option>
              <option value="bug-report">Bug Report</option>
              <option value="feature-request">Feature Request</option>
              <option value="data-issue">Data Issue</option>
              <option value="partnership">Partnership Inquiry</option>
              <option value="general">General Question</option>
              <option value="other">Other</option>
            </select>
          </div>
          
          <div class="form-group">
            <label for="message" class="form-label">Message</label>
            <textarea 
              id="message" 
              v-model="feedback.message"
              class="form-textarea"
              rows="5"
              placeholder="Tell us more about your inquiry..."
              required
            ></textarea>
          </div>
          
          <button type="submit" class="submit-button" :disabled="isSubmitting">
            {{ isSubmitting ? 'Sending...' : 'Send Feedback' }}
          </button>
        </form>
      </div>
    </section>
</div>
</template>
  
  
<script setup lang="ts">
import { ref } from 'vue';
import NavBar from "@/components/NavBar.vue";
import arjunImg from '@/assets/avatars/arjunmaitra.jpeg';
import stevenImg from '@/assets/avatars/stevenzhou.jpeg';
import ethanImg from '@/assets/avatars/ethanyang.jpeg';
import vivianImg from '@/assets/avatars/vivianguo.jpeg';

const isSubmitting = ref(false);

const feedback = ref({
  name: '',
  email: '',
  subject: '',
  message: ''
});

const teamMembers = [
  {
    name: 'Arjun Maitra',
    role: 'Head of Data Science',
    email: 'asm366@cornell.edu',
    linkedin: 'https://linkedin.com/in/arjun-maitra',
    avatar: arjunImg
  },
  {
    name: 'Steven Zhou',
    role: 'Data Scientist Emeritus',
    email: 'stevenzhouzihao@outlook.com',
    linkedin: 'https://www.linkedin.com/in/ste-z/',
    avatar: stevenImg
  },
  {
    name: 'Ethan Yang',
    role: 'Head of Marketing',
    email: 'ey283@cornell.edu',
    linkedin: 'https://www.linkedin.com/in/eycyang/',
    avatar: ethanImg
  },
  {
    name: 'Vivian Guo',
    role: 'Data Analyst',
    email: 'vjg32@cornell.edu',
    linkedin: 'https://www.linkedin.com/in/vivian-guo-5439b5329/',
    avatar: vivianImg
  }
];

const submitFeedback = async () => {
  if (!feedback.value.message.trim() || !feedback.value.subject) {
    alert('Please fill in both the subject and message fields.');
    return;
  }

  isSubmitting.value = true;
  
  // Create email content
  const emailSubject = `[${feedback.value.subject}] - Website Feedback`;
  const emailBody = `
Name: ${feedback.value.name || 'Not provided'}
Email: ${feedback.value.email || 'Not provided'}
Subject: ${feedback.value.subject}
Message: ${feedback.value.message}
  `.trim();

  // Create mailto link
  const mailtoLink = `mailto:support@ithacainsights.com?subject=${encodeURIComponent(emailSubject)}&body=${encodeURIComponent(emailBody)}`;
  
  // Open email client
  window.open(mailtoLink);
  
  // Reset form and show confirmation
  setTimeout(() => {
    alert('Thank you for your feedback! Your email client should open with a pre-filled message to support@ithacainsights.com');
    feedback.value = {
      name: '',
      email: '',
      subject: '',
      message: ''
    };
    isSubmitting.value = false;
  }, 500);
};

</script>

<style scoped>
/* Layout */
.contacts-section {
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

/* Contact Methods */
.contact-methods {
  padding: 0 2rem;
  width: 100%;
}

.contact-container {
  max-width: 1200px;
  margin: 0 auto;
}

.contact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.contact-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.contact-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.contact-icon {
  width: 60px;
  height: 60px;
  background: #e0e7ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
  color: #1e3a8a;
  font-size: 1.5rem;
}

.contact-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 1rem;
}

.contact-description {
  font-size: 1rem;
  color: #4b5563;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

.contact-link {
  display: inline-block;
  padding: 10px 20px;
  background: #1e3a8a;
  color: white;
  text-decoration: none;
  border-radius: 6px;
  font-weight: 500;
  transition: background 0.3s ease;
}

.contact-link:hover {
  background: #1d4ed8;
}

/* Team Contacts */
.team-contacts {
  padding: 2rem 5vw;
  background: #f8fafc;
  width: 100%;
}

.team-contacts-container {
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
}

.team-contacts-intro {
  font-size: 1.1rem;
  color: #4b5563;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.team-contacts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.team-contact-card {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.team-contact-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.team-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  margin: 0 auto 1rem;
  background: #e0e7ff;
}

.team-member-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: #1e3a8a;
  margin-bottom: 0.5rem;
}

.team-member-role {
  font-size: 1rem;
  color: #4b5563;
  margin-bottom: 1rem;
}

.team-contact-links {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.team-contact-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 6px 12px;
  background: #f1f5f9;
  color: #1e3a8a;
  text-decoration: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: background 0.3s ease;
}

.team-contact-link:hover {
  background: #e0e7ff;
}

/* Feedback Form */
.feedback-section {
  padding: 2rem 5vw;
  width: 100%;
}

.feedback-container {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
}

.feedback-intro {
  font-size: 1.1rem;
  color: #4b5563;
  margin-bottom: 3rem;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.feedback-form {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  text-align: left;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  font-size: 1rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 0.5rem;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #1e3a8a;
  box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 120px;
}

.submit-button {
  width: 100%;
  padding: 12px 24px;
  background: #1e3a8a;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.3s ease, transform 0.2s ease;
}

.submit-button:hover:not(:disabled) {
  background: #1d4ed8;
  transform: translateY(-1px);
}

.submit-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
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

  .contact-grid {
    grid-template-columns: 1fr;
  }

  .team-contacts-grid {
    grid-template-columns: 1fr;
  }

  .team-contact-links {
    flex-direction: column;
    align-items: center;
  }

  .feedback-form {
    padding: 1.5rem;
  }

  .contacts-section {
    gap: 40px;
  }
}

</style>
