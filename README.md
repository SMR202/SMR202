<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
  <img src="assets/hero-light.svg" width="100%" alt="Sameer Amjad. Indoor positioning, real-time systems and the web, built in Islamabad. An animated floor plan shows a phone's position estimate settling at the entrance, then walking a route to its destination.">
</picture>

I study computer science at FAST-NUCES in Islamabad. Most of my time goes into **TURN**, our final-year project: indoor navigation for malls and large buildings that works without installing beacons. My part is positioning, which means turning a phone's steps, heading and radio signals into a location you can trust. The map above is a small sketch of that.

Alongside it I research how digital twins stay in sync over unreliable networks, and I build websites and apps for businesses here, from a furniture storefront to a neuroscience institute.

### Right now

- Building TURN's positioning stack: step detection, heading and a particle filter that knows the floor plan.
- Designing experiments on MQTT QoS and edge buffering for digital-twin sync.
- Shipping NeuroZehn, a bilingual site for a brain-health institute.
- Building a customer feedback platform for local businesses and planning a school information system. Both are private for now.

### Selected work

<a href="https://github.com/SMR202/turn-indoor-navigation"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-turn-dark.svg"><img src="assets/work-turn-light.svg" width="100%" alt="TURN: indoor navigation for malls without installing beacons. I own positioning: step detection, heading, and a particle filter that rules out paths through walls."></picture></a>
<a href="https://github.com/ZakiNabeel/AI-System-for-Live-and-Recorded-Online-Video-Understanding-and-Summarization"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-lumen-dark.svg"><img src="assets/work-lumen-light.svg" width="100%" alt="Lumen: watches live streams or recorded videos, then transcribes, reads the frames, summarizes and answers questions about them through a ten-stage pipeline."></picture></a>
<a href="https://github.com/SMR202/dt-mqtt-resilience"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-twin-dark.svg"><img src="assets/work-twin-light.svg" width="100%" alt="Digital twins on bad networks: research on how MQTT QoS levels and edge buffering change freshness, delivery and recovery time when a cloud digital twin loses its connection."></picture></a>
<a href="https://github.com/SMR202/AirControlX"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-aircontrolx-dark.svg"><img src="assets/work-aircontrolx-light.svg" width="100%" alt="AirControlX: air traffic control simulation for three runways, run on POSIX threads with Unix pipes and drawn in SFML."></picture></a>
<a href="https://github.com/SMR202/Neurosphere-Global"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-neurozehn-dark.svg"><img src="assets/work-neurozehn-light.svg" width="100%" alt="NeuroZehn: a 61-page site for a brain-health institute, with Urdu right-to-left interface previews and accessible figures."></picture></a>
<a href="https://github.com/SMR202/IntegrityVerificationSystem"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-merkle-dark.svg"><img src="assets/work-merkle-light.svg" width="100%" alt="Integrity verification: SHA-256 Merkle trees over a million product reviews, with tamper detection and existence proofs checked in under 100 ms."></picture></a>
<a href="https://www.sameeramjad.xyz"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/work-clients-dark.svg"><img src="assets/work-clients-light.svg" width="100%" alt="Sites for Islamabad businesses: twenty-plus sites and pitch builds for cafés, salons, bakeries, a furniture maker, a school and a collector-car marketplace."></picture></a>

<details>
<summary><b>Sixteen more projects, from compilers to games</b></summary>

<br>

**Apps and platforms**

- **Busin.** React Native bus tracking with live GPS over WebSockets and an ETA for every stop. *Private repo.*
- **Skill-Link.** Kotlin marketplace for local services, with bids, chat with media and push notifications. *Private repo.*
- [**SkillLink, rebuilt**](https://github.com/SMR202/SkillLink-Java-Expo). The same marketplace on Spring Boot with JWT roles and an Expo client. Team project.
- [**SkillLink API**](https://github.com/SMR202/SkillLinkWebAPI). Express, Sequelize and MySQL behind the Kotlin app, with Cloudinary uploads and Firebase messaging.
- [**Centaurus Experience**](https://github.com/SMR202/centaurus-experience). Expo prototype of a visitor app for The Centaurus Mall: directory, indoor directions, rewards and finding your car.
- [**Lakkar Home**](https://github.com/SMR202/Lakkar-Website). Furniture storefront with cash-on-delivery checkout, run entirely from the owner's Google Sheet.

**AI and automation**

- [**RACE reading comprehension**](https://github.com/SMR202/RACE-Reading-Comprehension-AI). Classical ML that checks answers and generates distractors and hints for reading quizzes.
- [**AI Resume Tailor**](https://github.com/SMR202/AiResumeTailor). Rewrites a resume for a specific job description through an n8n workflow and hands back a PDF.
- **Reddit to YouTube pipeline.** An n8n workflow that picks stories, rewrites them with Gemini, voices them with Azure TTS, renders with Remotion and uploads on a schedule.

**Compilers, systems and data structures**

- [**LL(1) parser**](https://github.com/SMR202/LL-1-Parser). FIRST and FOLLOW sets, left-recursion removal, left factoring and parse trees in C++17.
- [**Git-Lite**](https://github.com/FatimaSohailll/Git-Lite). Version control on AVL, red-black and B-trees with Merkle-tree change tracking. Team project.
- [**Terminal NotePad**](https://github.com/SMR202/Terminal-NotePad). A command-line text editor in C++ with word suggestions and search.

**Desktop**

- [**SafeNest**](https://github.com/SMR202/SafeNest). JavaFX home-security dashboard for cameras, sensors and PIN-protected alarm modes.
- [**TravelEase**](https://github.com/SMR202/TravelEase). Travel booking in C# Windows Forms on SQL Server, with reports and triggers.

**Games**

- [**Plants vs. Zombies, in C++**](https://github.com/SMR202/PlantsVsZombies). Tower defence with factories for six plants and five zombies, built on SFML.
- [**Centipede, in C++**](https://github.com/SMR202/ATARI-Centipede). The arcade game rebuilt in SFML, one of my first C++ projects.

</details>

### Tools I use

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/tools-dark.svg">
  <img src="assets/tools-light.svg" width="100%" alt="Tools I use. Languages: TypeScript, C++, Python, Kotlin, Java, C# and .NET. Web: Next.js, React, Tailwind CSS, Node.js, Express, Sanity. Apps and APIs: Expo, Android, Spring Boot, FastAPI, Firebase. Data: PostgreSQL, Supabase, MySQL, MongoDB, Google Sheets. ML and media: scikit-learn, Gemini, FFmpeg, Streamlit. Systems: Linux, Git, Docker, MQTT, n8n, SFML.">
</picture>

### Activity

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/activity-dark.svg">
  <img src="assets/activity-light.svg" width="100%" alt="My GitHub contributions over the last year, refreshed daily.">
</picture>

### Get in touch

<a href="https://www.sameeramjad.xyz"><img src="assets/contact-portfolio.svg" width="32%" alt="Portfolio: sameeramjad.xyz"></a>
<a href="https://www.linkedin.com/in/sameeramjd"><img src="assets/contact-linkedin.svg" width="32%" alt="LinkedIn: in/sameeramjd"></a>
<a href="mailto:sameeramjad202@gmail.com"><img src="assets/contact-email.svg" width="32%" alt="Email: sameeramjad202@gmail.com"></a>

<sub>Every image on this page is drawn by the scripts in <a href="scripts">scripts/</a>. The activity panel is redrawn each night by a GitHub Action.</sub>
