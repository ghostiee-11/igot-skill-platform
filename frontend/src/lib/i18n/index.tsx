"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

type Language = "en" | "hi";

interface Translations {
  [key: string]: {
    en: string;
    hi: string;
  };
}

const translations: Translations = {
  // Navigation
  "nav.brand": { en: "iGOT Karmayogi", hi: "आईगॉट कर्मयोगी" },
  "nav.subBrand": {
    en: "Official Statistical & Civil Service Learning",
    hi: "आधिकारिक सांख्यिकी एवं सिविल सेवा शिक्षण",
  },
  "nav.about": { en: "About", hi: "परिचय" },
  "nav.howItWorks": { en: "How it Works", hi: "यह कैसे कार्य करता है" },
  "nav.resources": { en: "Resources", hi: "संसाधन" },
  "nav.help": { en: "Help", hi: "सहायता" },
  "nav.discover": { en: "Discover", hi: "अन्वेषण करें" },
  "nav.myLearning": { en: "My Learning", hi: "मेरी शिक्षा" },
  "nav.search": { en: "Search Catalogue", hi: "पाठ्यक्रम खोजें" },
  "nav.admin": { en: "Administration", hi: "प्रशासन" },
  "nav.profile": { en: "My Profile", hi: "मेरी प्रोफ़ाइल" },
  "nav.settings": { en: "Settings", hi: "सेटिंग्स" },
  "nav.logout": { en: "Sign Out", hi: "लॉग आउट" },
  "nav.login": { en: "Sign In", hi: "लॉग इन" },
  "nav.register": { en: "Register", hi: "पंजीकरण" },
  "nav.labs": { en: "Virtual Labs", hi: "वर्चुअल लैब्स" },
  "nav.dashboard": { en: "Dashboard", hi: "डैशबोर्ड" },
  "nav.courses": { en: "Courses", hi: "पाठ्यक्रम" },
  "nav.oralBoard": { en: "AI Oral Board", hi: "एआई मौखिक बोर्ड" },
  "nav.adaptiveExam": { en: "Adaptive Exam", hi: "अनुकूली परीक्षा" },
  "nav.digitalGovernance": { en: "Digital Governance", hi: "डिजिटल शासन" },
  "nav.cyberSandbox": { en: "Cyber Sandbox", hi: "साइबर सैंडबॉक्स" },
  "nav.scenarios": { en: "Incident Scenarios", hi: "घटना परिदृश्य" },

  // Home Dashboard (Post-Login)
  "home.eyebrow": {
    en: "Official Cadre Dashboard • Ministry of Statistics & Programme Implementation",
    hi: "आधिकारिक संवर्ग डैशबोर्ड • सांख्यिकी एवं कार्यक्रम कार्यान्वयन मंत्रालय",
  },
  "home.welcome": { en: "Welcome back", hi: "पुनः स्वागत है" },
  "home.trainingRecord": {
    en: "Official Statistical Cadre Training Record",
    hi: "आधिकारिक सांख्यिकी संवर्ग प्रशिक्षण रिकॉर्ड",
  },
  "home.browseCatalogue": {
    en: "Browse Catalogue",
    hi: "पाठ्यक्रम सूची देखें",
  },
  "home.myLearningBtn": { en: "My Learning", hi: "मेरी शिक्षा" },
  "home.continueLearning": { en: "Continue Learning", hi: "सीखना जारी रखें" },
  "home.activeCoursework": {
    en: "Resume your active coursework right where you paused",
    hi: "अपना सक्रिय अध्ययन वहीं से जारी रखें जहां आपने विराम लिया था",
  },
  "home.resumeCourse": { en: "Resume Lesson", hi: "पाठ पुनः शुरू करें" },
  "home.inProgress": { en: "In Progress", hi: "प्रगति पर" },
  "home.completed": { en: "Completed", hi: "पूर्ण" },
  "home.courseCompletion": { en: "Course Completion", hi: "पाठ्यक्रम पूर्णता" },
  "home.noCourseInProgress": {
    en: "You do not currently have any course in progress.",
    hi: "वर्तमान में आपका कोई पाठ्यक्रम प्रगति पर नहीं है।",
  },
  "home.exploreEnroll": {
    en: "Explore & Enroll in Courses",
    hi: "पाठ्यक्रम खोजें एवं नामांकन करें",
  },
  "home.todaysGoals": {
    en: "Today's Learning Goal",
    hi: "आज का अध्ययन लक्ष्य",
  },
  "home.dailyGoalAchieved": {
    en: "Daily public service study goal achieved!",
    hi: "दैनिक लोक सेवा अध्ययन लक्ष्य पूर्ण हुआ!",
  },
  "home.minutesRemaining": {
    en: "{minutes} minutes remaining today",
    hi: "आज {minutes} मिनट शेष हैं",
  },
  "home.learningStreak": { en: "Learning Streak", hi: "अध्ययन निरंतरता" },
  "home.activeDailyEngagement": {
    en: "Active Daily Engagement",
    hi: "सक्रिय दैनिक सहभागिता",
  },
  "home.days": { en: "Days Active", hi: "दिन सक्रिय" },
  "home.targetMinutes": { en: "target today", hi: "आज का लक्ष्य" },
  "home.recommended": {
    en: "Recommended For Your Ministry",
    hi: "आपके मंत्रालय हेतु अनुशंसित",
  },
  "home.recommendedSubtitle": {
    en: "Curated for your statistical cadre based on your ministry onboarding profile",
    hi: "आपके मंत्रालय ऑनबोर्डिंग प्रोफाइल के आधार पर आपके सांख्यिकी संवर्ग हेतु तैयार",
  },
  "home.viewAll": { en: "View All", hi: "सभी देखें" },
  "home.inspectCourse": { en: "Inspect Course", hi: "पाठ्यक्रम देखें" },
  "home.trending": { en: "Trending Courses", hi: "प्रचलित पाठ्यक्रम" },
  "home.trendingSubtitle": {
    en: "Popular training modules across central and state ministries",
    hi: "केंद्रीय एवं राज्य मंत्रालयों में लोकप्रिय प्रशिक्षण मॉड्यूल",
  },
  "home.civilServantsEnrolled": {
    en: "civil servants enrolled",
    hi: "सिविल सेवक नामांकित",
  },
  "home.futurePlanned": {
    en: "Future Planned Courses",
    hi: "आगामी नियोजित पाठ्यक्रम",
  },
  "home.futurePlannedSubtitle": {
    en: "Queued capacity building modules for upcoming quarters",
    hi: "आगामी तिमाहियों हेतु नियोजित क्षमता निर्माण मॉड्यूल",
  },
  "home.target": { en: "Target:", hi: "लक्ष्य:" },
  "home.scheduledBy": { en: "Scheduled by", hi: "द्वारा निर्धारित" },
  "home.departmentAdmin": { en: "Department Admin", hi: "विभागीय व्यवस्थापक" },
  "home.self": { en: "Self", hi: "स्वयं" },
  "home.viewSyllabus": { en: "View Syllabus", hi: "पाठ्यक्रम देखें" },
  "home.noFutureCourses": {
    en: "No future courses scheduled yet.",
    hi: "अभी तक कोई आगामी पाठ्यक्रम निर्धारित नहीं है।",
  },
  "home.myProgress": {
    en: "Learning Progress Snapshot",
    hi: "प्रगति संक्षिप्त विवरण",
  },
  "home.fullRecord": { en: "Full Record", hi: "संपूर्ण विवरण" },
  "home.learningHours": { en: "Learning Hours", hi: "अध्ययन घंटे" },
  "home.competencies": { en: "Acquired Competencies", hi: "अर्जित दक्षताएं" },
  "home.competencyRadar": { en: "Competency Radar", hi: "दक्षता रडार" },
  "home.completeAssessmentsMsg": {
    en: "Complete assessments to earn verified statistical competencies.",
    hi: "सत्यापित सांख्यिकी दक्षताएं अर्जित करने के लिए मूल्यांकन पूर्ण करें।",
  },
  "home.recentlyExplored": {
    en: "Recently Explored",
    hi: "हाल ही में देखे गए",
  },

  // Learning Transcript (My Learning)
  "learning.eyebrow": {
    en: "Official Learning Transcript • National Cadre Records",
    hi: "आधिकारिक शिक्षण प्रतिलेख • राष्ट्रीय संवर्ग अभिलेख",
  },
  "learning.title": {
    en: "My Learning & Cadre Records",
    hi: "मेरी शिक्षा एवं संवर्ग अभिलेख",
  },
  "learning.subtitle": {
    en: "Personalized training ledger, competency growth, and verified credentials",
    hi: "व्यक्तिगत प्रशिक्षण खाता, दक्षता विकास और सत्यापित क्रेडेंशियल",
  },
  "learning.tabInProgress": {
    en: "In Progress Courses",
    hi: "प्रगतिशील पाठ्यक्रम",
  },
  "learning.tabCompleted": {
    en: "Completed Certifications",
    hi: "पूर्ण प्रमाणन",
  },
  "learning.tabSkills": { en: "Acquired Competencies", hi: "अर्जित दक्षताएं" },
  "learning.tabPlanned": {
    en: "Queued Learning Goals",
    hi: "नियोजित अध्ययन लक्ष्य",
  },
  "learning.viewCertificate": {
    en: "View Official Certificate",
    hi: "आधिकारिक प्रमाणपत्र देखें",
  },
  "learning.resume": { en: "Resume Course", hi: "पाठ्यक्रम जारी रखें" },
  "learning.noCompleted": {
    en: "No completed courses yet. Pass certification assessments to earn credentials.",
    hi: "अभी तक कोई पूर्ण पाठ्यक्रम नहीं है। क्रेडेंशियल अर्जित करने के लिए प्रमाणन मूल्यांकन उत्तीर्ण करें।",
  },
  "learning.noSkills": {
    en: "No competencies recorded yet. Complete course modules to build skills.",
    hi: "अभी तक कोई दक्षता दर्ज नहीं है। कौशल निर्माण के लिए पाठ्यक्रम मॉड्यूल पूर्ण करें।",
  },
  "learning.noPlanned": {
    en: "No planned courses queued.",
    hi: "कोई आगामी पाठ्यक्रम निर्धारित नहीं है।",
  },

  // Profile Management
  "profile.eyebrow": {
    en: "Ministry of Statistics & Programme Implementation • Official Personnel Record",
    hi: "सांख्यिकी एवं कार्यक्रम कार्यान्वयन मंत्रालय • आधिकारिक कार्मिक रिकॉर्ड",
  },
  "profile.title": {
    en: "Official Civil Service Profile",
    hi: "आधिकारिक सिविल सेवा प्रोफ़ाइल",
  },
  "profile.subtitle": {
    en: "Manage your central service credentials, departmental placement, and portal preferences.",
    hi: "अपने केंद्रीय सेवा क्रेडेंशियल, विभागीय पदस्थापना और पोर्टल प्राथमिकताओं का प्रबंधन करें।",
  },
  "profile.verifiedOfficial": {
    en: "Verified Official",
    hi: "सत्यापित अधिकारी",
  },
  "profile.officialRole": {
    en: "Official Role & Organizational Placement",
    hi: "आधिकारिक भूमिका एवं संगठनात्मक पदस्थापना",
  },
  "profile.officialRoleDesc": {
    en: "Sourced from your onboarding record; fully editable as responsibilities evolve.",
    hi: "आपके ऑनबोर्डिंग रिकॉर्ड से प्राप्त; जिम्मेदारियों के विकास के साथ संपादन योग्य।",
  },
  "profile.fullName": { en: "Full Name", hi: "पूरा नाम" },
  "profile.phone": { en: "Phone / WhatsApp", hi: "फ़ोन / व्हाट्सएप" },
  "profile.designation": { en: "Official Designation", hi: "आधिकारिक पदनाम" },
  "profile.department": { en: "Ministry / Department", hi: "मंत्रालय / विभाग" },
  "profile.jobRole": { en: "Job Role", hi: "कार्य भूमिका" },
  "profile.yearsInService": { en: "Years in Service", hi: "सेवा वर्ष" },
  "profile.currentAssignment": {
    en: "Current Active Project / Assignment",
    hi: "वर्तमान सक्रिय परियोजना / कार्यभार",
  },
  "profile.qualifications": {
    en: "Academic Qualifications & Prior Training",
    hi: "शैक्षणिक योग्यताएं एवं पूर्व प्रशिक्षण",
  },
  "profile.preferences": {
    en: "Portal Preferences & Study Target",
    hi: "पोर्टल प्राथमिकताएं एवं अध्ययन लक्ष्य",
  },
  "profile.preferencesDesc": {
    en: "Configure interface language, appearance, and study targets",
    hi: "इंटरफ़ेस भाषा, स्वरूप और अध्ययन लक्ष्यों को कॉन्फ़िगर करें",
  },
  "profile.interfaceLanguage": {
    en: "Portal Interface Language",
    hi: "पोर्टल इंटरफ़ेस भाषा",
  },
  "profile.dailyGoal": {
    en: "Daily Study Goal (Minutes)",
    hi: "दैनिक अध्ययन लक्ष्य (मिनट)",
  },
  "profile.saveChanges": {
    en: "Save Profile Settings",
    hi: "प्रोफ़ाइल सेटिंग्स सहेजें",
  },
  "profile.saving": {
    en: "Saving Changes...",
    hi: "परिवर्तन सहेजे जा रहे हैं...",
  },
  "profile.savedSuccess": {
    en: "Profile Updated Successfully",
    hi: "प्रोफ़ाइल सफलतापूर्वक अपडेट की गई",
  },

  // Central Administration
  "admin.eyebrow": {
    en: "Central Administration & Cadre Oversight • Capacity Building Commission",
    hi: "केंद्रीय प्रशासन एवं संवर्ग पर्यवेक्षण • क्षमता निर्माण आयोग",
  },
  "admin.title": {
    en: "Capacity Building Admin Console",
    hi: "क्षमता निर्माण व्यवस्थापक कंसोल",
  },
  "admin.subtitle": {
    en: "Supervise cadre training progress, assign official courses, and audit question difficulty.",
    hi: "संवर्ग प्रशिक्षण प्रगति का पर्यवेक्षण करें, आधिकारिक पाठ्यक्रम सौंपें और प्रश्न स्तर का ऑडिट करें।",
  },
  "admin.authorityBadge": {
    en: "Administrative Authority",
    hi: "प्रशासनिक प्राधिकार",
  },
  "admin.addNewCourse": { en: "Add New Course", hi: "नया पाठ्यक्रम जोड़ें" },
  "admin.registeredOfficials": {
    en: "Registered Officials",
    hi: "पंजीकृत अधिकारी",
  },
  "admin.activeCurricula": { en: "Active Curricula", hi: "सक्रिय पाठ्यक्रम" },
  "admin.completionRate": {
    en: "Cadre Completion Rate",
    hi: "संवर्ग पूर्णता दर",
  },
  "admin.passRate": { en: "Assessment Pass Rate", hi: "मूल्यांकन उत्तीर्ण दर" },
  "admin.cadreManagement": {
    en: "Civil Servants Cadre Management & Assignment",
    hi: "सिविल सेवक संवर्ग प्रबंधन एवं कार्यभार",
  },
  "admin.cadreManagementDesc": {
    en: "Monitor active enrollments per official and assign mandatory statistical training",
    hi: "प्रति अधिकारी सक्रिय नामांकनों की निगरानी करें और अनिवार्य सांख्यिकीय प्रशिक्षण सौंपें",
  },
  "admin.colOfficial": { en: "Official", hi: "अधिकारी" },
  "admin.colDeptRole": { en: "Department & Role", hi: "विभाग एवं भूमिका" },
  "admin.colOnboarded": { en: "Onboarded", hi: "ऑनबोर्ड स्थिति" },
  "admin.colEnrolled": { en: "Enrolled Courses", hi: "नामांकित पाठ्यक्रम" },
  "admin.colActions": { en: "Actions", hi: "कार्यवाही" },
  "admin.assignCourse": { en: "Assign Course", hi: "पाठ्यक्रम सौंपें" },
  "admin.completed": { en: "Completed", hi: "पूर्ण" },
  "admin.pending": { en: "Pending", hi: "लंबित" },
  "admin.noActiveCourses": {
    en: "No active courses",
    hi: "कोई सक्रिय पाठ्यक्रम नहीं",
  },
  "admin.questionAnalytics": {
    en: "Assessment Question Difficulty Analytics",
    hi: "मूल्यांकन प्रश्न कठिनाई विश्लेषण",
  },
  "admin.questionAnalyticsDesc": {
    en: "Pinpoints exact methodology concepts where officials struggle across nationwide exams",
    hi: "उन सटीक पद्धतिगत अवधारणाओं को इंगित करता है जहां राष्ट्रव्यापी परीक्षाओं में अधिकारियों को कठिनाई होती है",
  },

  // Discover & Search
  "discover.eyebrow": {
    en: "Official Course Catalogue • Ministry of Statistics & Programme Implementation",
    hi: "आधिकारिक पाठ्यक्रम सूची • सांख्यिकी एवं कार्यक्रम कार्यान्वयन मंत्रालय",
  },
  "discover.title": {
    en: "Course Catalogue & External Training",
    hi: "पाठ्यक्रम सूची एवं बाह्य प्रशिक्षण",
  },
  "discover.subtitle": {
    en: "Empowering Indian Civil Servants with Certified Official Statistical Competencies",
    hi: "भारतीय सिविल सेवकों को प्रमाणित आधिकारिक सांख्यिकी दक्षताओं से सशक्त बनाना",
  },
  "discover.searchPlaceholder": {
    en: "Search by course title, methodology, or ministry...",
    hi: "शीर्षक, पद्धति या मंत्रालय द्वारा खोजें...",
  },
  "discover.searchBtn": { en: "Search", hi: "खोजें" },
  "discover.clearSearch": { en: "Clear Search", hi: "साफ़ करें" },
  "discover.trending": { en: "Trending Topics:", hi: "प्रचलित विषय:" },
  "discover.recent": { en: "Recent:", hi: "हाल की खोज:" },
  "discover.all": { en: "All Disciplines", hi: "सभी विषय" },
  "discover.popular": { en: "Popular", hi: "लोकप्रिय" },
  "discover.new": { en: "New Releases", hi: "नए संस्करण" },
  "discover.filters": { en: "Filters", hi: "फ़िल्टर" },
  "discover.source": { en: "Provider Source", hi: "प्रदाता स्रोत" },
  "discover.allProviders": { en: "All Providers", hi: "सभी प्रदाता" },
  "discover.mospiInternal": {
    en: "MoSPI Internal Only",
    hi: "केवल एमओएसपीआई आंतरिक",
  },
  "discover.externalAccredited": {
    en: "External Accredited (ISTM/DoPT)",
    hi: "बाह्य मान्यता प्राप्त (आईएसटीएम/डीओपीटी)",
  },
  "discover.difficulty": { en: "Difficulty Level", hi: "कठिनाई स्तर" },
  "discover.allDifficulties": { en: "All Difficulties", hi: "सभी कठिनाई स्तर" },
  "discover.beginner": { en: "Beginner", hi: "प्रारंभिक" },
  "discover.intermediate": { en: "Intermediate", hi: "मध्यम" },
  "discover.advanced": { en: "Advanced", hi: "उन्नत" },
  "discover.sort": { en: "Sort By", hi: "क्रमबद्ध करें" },
  "discover.sortPopular": { en: "Most Enrolled", hi: "सर्वाधिक नामांकित" },
  "discover.sortRating": { en: "Highest Rated", hi: "सर्वोच्च मूल्यांकित" },
  "discover.sortNew": { en: "Newly Published", hi: "हाल ही में प्रकाशित" },
  "discover.sortDuration": { en: "Shortest Duration", hi: "न्यूनतम अवधि" },
  "discover.resultsCount": {
    en: "Accredited Courses",
    hi: "मान्यता प्राप्त पाठ्यक्रम",
  },
  "discover.showingSingle": {
    en: "Showing 1 accredited course",
    hi: "1 मान्यता प्राप्त पाठ्यक्रम प्रदर्शित",
  },
  "discover.showingMultiple": {
    en: "Showing {count} accredited courses",
    hi: "{count} मान्यता प्राप्त पाठ्यक्रम प्रदर्शित",
  },
  "discover.noCoursesFound": {
    en: "No matching courses found",
    hi: "कोई मेल खाता पाठ्यक्रम नहीं मिला",
  },
  "discover.noCoursesDesc": {
    en: "Try adjusting your search keyword or clearing selected difficulty and provider filters.",
    hi: "कृपया अपने खोज शब्द को बदलें या चयनित फ़िल्टर रीसेट करें।",
  },
  "discover.resetFilters": {
    en: "Reset All Filters",
    hi: "सभी फ़िल्टर रीसेट करें",
  },
  "discover.updating": {
    en: "Updating course catalogue...",
    hi: "पाठ्यक्रम सूची लोड हो रही है...",
  },
  "discover.internalBadge": { en: "MoSPI Internal", hi: "एमओएसपीआई आंतरिक" },
  "discover.externalBadge": { en: "ISTM External", hi: "आईएसटीएम बाह्य" },
  "discover.hours": { en: "Hours", hi: "घंटे" },
  "discover.accreditedBody": {
    en: "Accredited Body:",
    hi: "मान्यता प्राप्त संस्था:",
  },
  "discover.targetDifficulty": { en: "Target Level:", hi: "लक्षित स्तर:" },
  "discover.modules": { en: "Curriculum:", hi: "पाठ्यक्रम:" },
  "discover.units": { en: "Modules", hi: "मॉड्यूल" },
  "discover.enrolled": { en: "enrolled", hi: "नामांकित" },
  "discover.viewCourse": { en: "View Course", hi: "पाठ्यक्रम देखें" },
  "discover.trustTag1": {
    en: "MoSPI Accredited Curriculum",
    hi: "एमओएसपीआई मान्यता प्राप्त पाठ्यक्रम",
  },
  "discover.trustTag2": {
    en: "CBC Competency Standards",
    hi: "सीबीसी क्षमता मानक",
  },
  "discover.trustTag3": {
    en: "Verifiable Service Credentials",
    hi: "सत्यापन योग्य सेवा क्रेडेंशियल",
  },

  // Catalog Categories
  "category.Sample Surveys": { en: "Sample Surveys", hi: "नमूना सर्वेक्षण" },
  "category.Price Statistics": {
    en: "Price Statistics",
    hi: "मूल्य सांख्यिकी",
  },
  "category.Data Governance": { en: "Data Governance", hi: "डेटा प्रशासन" },
  "category.Public Administration": {
    en: "Public Administration",
    hi: "लोक प्रशासन",
  },
  "category.Data Science": { en: "Data Science", hi: "डेटा विज्ञान" },

  // Trending Topics
  "topic.National Sample Survey": {
    en: "National Sample Survey",
    hi: "राष्ट्रीय नमूना सर्वेक्षण",
  },
  "topic.Consumer Price Index": {
    en: "Consumer Price Index",
    hi: "उपभोक्ता मूल्य सूचकांक",
  },
  "topic.CAPI Field Validation": {
    en: "CAPI Field Validation",
    hi: "सीएपीआई क्षेत्रीय सत्यापन",
  },
  "topic.UN-NQAF Data Quality": {
    en: "UN-NQAF Data Quality",
    hi: "यूएन-एनक्यूएएफ डेटा गुणवत्ता",
  },
  "topic.Treasury Single Account PFMS": {
    en: "Treasury Single Account PFMS",
    hi: "एकल नोडल खाता (पीएफएमएस)",
  },
  "topic.Python Microdata Analysis": {
    en: "Python Microdata Analysis",
    hi: "पायथन माइक्रोडाटा विश्लेषण",
  },

  // Course Titles & Overviews
  "course.1.title": {
    en: "Fundamentals of National Sample Surveys (NSS)",
    hi: "राष्ट्रीय नमूना सर्वेक्षण (एनएसएस) के मूलभूत सिद्धांत",
  },
  "course.1.overview": {
    en: "Master the methodological framework of large-scale socio-economic surveys conducted by India's National Sample Survey Office (NSSO). Covers multi-stage stratified sampling, field schedules, non-sampling error minimization, and computer-assisted personal interviewing (CAPI).",
    hi: "भारत के राष्ट्रीय नमूना सर्वेक्षण कार्यालय (एनएसएसओ) द्वारा आयोजित बड़े पैमाने के सामाजिक-आर्थिक सर्वेक्षणों के पद्धतिगत ढांचे में दक्षता। बहु-स्तरीय स्तरीकृत नमूनाकरण, फील्ड शेड्यूल, गैर-नमूनाकरण त्रुटि न्यूनीकरण और कंप्यूटर-सहायता प्राप्त व्यक्तिगत साक्षात्कार (सीएपीआई)।",
  },
  "course.2.title": {
    en: "Compilation of Consumer Price Index (CPI) & Inflation Metrics",
    hi: "उपभोक्ता मूल्य सूचकांक (सीपीआई) संकलन एवं मुद्रास्फीति मेट्रिक्स",
  },
  "course.2.overview": {
    en: "Comprehensive practical guide to the compilation of All India Consumer Price Index (Rural, Urban, Combined). Learn item basket weighting, Laspeyres index formulation, geometric mean of price relatives, treatment of seasonal goods, and house rent imputation.",
    hi: "अखिल भारतीय उपभोक्ता मूल्य सूचकांक (ग्रामीण, शहरी, संयुक्त) के संकलन की व्यापक व्यावहारिक मार्गदर्शिका। वस्तु टोकरी भारांकन, लास्पेयर्स सूचकांक निर्माण, मूल्य अनुपातों का ज्यामितीय माध्य, मौसमी वस्तुओं का प्रबंधन और मकान किराया आरोपण सीखें।",
  },
  "course.3.title": {
    en: "Data Quality Frameworks & Official Statistics in India",
    hi: "डेटा गुणवत्ता रूपरेखा एवं भारत में आधिकारिक सांख्यिकी",
  },
  "course.3.overview": {
    en: "Aligning Indian official statistics with the United Nations National Quality Assurance Framework (UN-NQAF). Study the 19 principles of statistical integrity, confidentiality safeguards, revision policies, and metadata standards.",
    hi: "भारतीय आधिकारिक सांख्यिकी को संयुक्त राष्ट्र राष्ट्रीय गुणवत्ता आश्वासन रूपरेखा (यूएन-एनक्यूएएफ) के अनुरूप बनाना। सांख्यिकीय सत्यनिष्ठा के 19 सिद्धांतों, गोपनीयता सुरक्षा उपायों, संशोधन नीतियों और मेटाडेटा मानकों का अध्ययन करें।",
  },
  "course.4.title": {
    en: "Digital Governance & Public Financial Management System (PFMS)",
    hi: "डिजिटल प्रशासन एवं सार्वजनिक वित्तीय प्रबंधन प्रणाली (पीएफएमएस)",
  },
  "course.4.overview": {
    en: "Direct Benefit Transfer (DBT), treasury integration, electronic bill processing, and expenditure tracking through PFMS. Authorized course accredited by ISTM for all central government employees.",
    hi: "प्रत्यक्ष लाभ अंतरण (डीबीटी), राजकोष एकीकरण, इलेक्ट्रॉनिक बिल प्रसंस्करण और पीएफएमएस के माध्यम से व्यय ट्रैकिंग। सभी केंद्रीय सरकारी कर्मचारियों के लिए आईएसटीएम द्वारा मान्यता प्राप्त अधिकृत पाठ्यक्रम।",
  },
  "course.5.title": {
    en: "Python and Statistical Computing for Public Policy",
    hi: "लोक नीति हेतु पायथन एवं सांख्यिकीय संगणना",
  },
  "course.5.overview": {
    en: "Modern data analysis for official statisticians using Pandas, NumPy, and Statsmodels. Automate data cleaning, compute econometric models, and generate reproducible policy briefs.",
    hi: "पांडास, नम्पाय और स्टैट्समॉडल्स का उपयोग कर आधिकारिक सांख्यिकीविदों हेतु आधुनिक डेटा विश्लेषण। डेटा सफाई स्वचालित करें, अर्थमितीय मॉडल तैयार करें और प्रतिलिपि प्रस्तुत करने योग्य नीति संक्षिप्त विवरण तैयार करें।",
  },

  // Accredited Organizations
  "org.National Sample Survey Office (NSSO)": {
    en: "National Sample Survey Office (NSSO)",
    hi: "राष्ट्रीय नमूना सर्वेक्षण कार्यालय (एनएसएसओ)",
  },
  "org.Central Statistics Office (CSO)": {
    en: "Central Statistics Office (CSO)",
    hi: "केंद्रीय सांख्यिकी कार्यालय (सीएसओ)",
  },
  "org.National Statistical Systems Training Academy (NSSTA)": {
    en: "National Statistical Systems Training Academy (NSSTA)",
    hi: "राष्ट्रीय सांख्यिकी प्रणाली प्रशिक्षण अकादमी (एनएसएसटीए)",
  },
  "org.Institute of Secretariat Training & Management (ISTM)": {
    en: "Institute of Secretariat Training & Management (ISTM)",
    hi: "सचिवालय प्रशिक्षण एवं प्रबंधन संस्थान (आईएसटीएम)",
  },
  "org.MoSPI Data Lab": {
    en: "MoSPI Data Lab",
    hi: "सांख्यिकी मंत्रालय डेटा लैब",
  },

  // Course Page
  "course.enrollNow": {
    en: "Enroll in Course",
    hi: "पाठ्यक्रम में प्रवेश लें",
  },
  "course.startLearning": { en: "Start Learning", hi: "सीखना शुरू करें" },
  "course.continue": { en: "Continue Learning", hi: "अध्ययन जारी रखें" },
  "course.resume": { en: "Resume Coursework", hi: "अध्ययन जारी रखें" },
  "course.resumeCourse": { en: "Resume Course", hi: "पाठ्यक्रम जारी रखें" },
  "course.syllabus": {
    en: "Course Syllabus & Curriculum",
    hi: "पाठ्यक्रम रूपरेखा एवं विषय-सूची",
  },
  "course.skillsGained": { en: "Competencies Acquired", hi: "अर्जित क्षमताएं" },
  "course.instructor": { en: "Faculty / Instructor", hi: "संकाय / प्रशिक्षक" },
  "course.organization": {
    en: "Accredited Body",
    hi: "मान्यता प्राप्त संस्था",
  },
  "course.duration": { en: "Estimated Duration", hi: "अनुमानित अवधि" },
  "course.learningHours": { en: "Learning Hours", hi: "अध्ययन घंटे" },
  "course.officialRating": { en: "Official Rating", hi: "आधिकारिक रेटिंग" },
  "course.enrolled": { en: "enrolled", hi: "नामांकित" },
  "course.completed": { en: "Completed", hi: "पूर्ण" },
  "course.takeAssessment": {
    en: "Take Certification Assessment",
    hi: "प्रमाणन मूल्यांकन दें",
  },
  "course.materials": {
    en: "Course Materials Breakdown",
    hi: "पाठ्यक्रम सामग्री विवरण",
  },
  "course.materialsIncluded": { en: "Materials included", hi: "शामिल सामग्री" },
  "course.readings": { en: "Readings", hi: "पठन सामग्री" },
  "course.videos": { en: "Videos", hi: "वीडियो" },
  "course.officialCertificate": { en: "Official certificate", hi: "आधिकारिक प्रमाणपत्र" },
  "course.accredited": { en: "Accredited", hi: "मान्यताप्राप्त" },
  "course.videoLectures": { en: "Video Lectures", hi: "वीडियो व्याख्यान" },
  "course.readingModules": { en: "Reading Modules", hi: "पठन मॉड्यूल" },
  "course.practicalLabs": {
    en: "Practical CAPI/Python Labs",
    hi: "व्यावहारिक सीएपीआई/पायथन लैब्स",
  },
  "course.mcqTest": {
    en: "MCQ Certification Test",
    hi: "एमसीक्यू प्रमाणन परीक्षा",
  },
  "course.lessons": { en: "lessons", hi: "पाठ" },
  "course.includesPractice": { en: "Includes Practice", hi: "अभ्यास शामिल है" },
  "course.backToCatalogue": {
    en: "Back to Catalogue",
    hi: "सूची पर वापस जाएं",
  },
  "course.notFound": { en: "Course Not Found", hi: "पाठ्यक्रम नहीं मिला" },
  "course.notFoundDesc": {
    en: "The requested course could not be retrieved from the national database.",
    hi: "अनुरोधित पाठ्यक्रम राष्ट्रीय डेटाबेस से प्राप्त नहीं किया जा सका।",
  },

  // Learning Player
  "learn.markCompleted": {
    en: "Mark Completed & Next",
    hi: "पूर्ण चिह्नित करें और आगे बढ़ें",
  },
  "learn.previous": { en: "Previous Lesson", hi: "पिछला पाठ" },
  "learn.next": { en: "Next Lesson", hi: "अगला पाठ" },
  "learn.practice": {
    en: "In-Lesson Concept Activity",
    hi: "पाठ-अंतर्गत संकल्पना अभ्यास",
  },
  "learn.checkAnswer": { en: "Validate Concept", hi: "उत्तर की पुष्टि करें" },
  "learn.takeAssessment": {
    en: "Proceed to Final Assessment",
    hi: "अंतिम मूल्यांकन की ओर बढ़ें",
  },

  // Assessments
  "assess.instructions": {
    en: "Assessment Instructions",
    hi: "मूल्यांकन निर्देश",
  },
  "assess.passRequirement": { en: "Passing Standard", hi: "उत्तीर्ण मानक" },
  "assess.timeLimit": { en: "Time Allotted", hi: "आवंटित समय" },
  "assess.startAssessment": {
    en: "Begin Official Assessment",
    hi: "आधिकारिक मूल्यांकन प्रारंभ करें",
  },
  "assess.submit": { en: "Submit Examination", hi: "परीक्षा जमा करें" },
  "assess.congratulations": {
    en: "Assessment Passed!",
    hi: "मूल्यांकन उत्तीर्ण!",
  },
  "assess.tryAgain": {
    en: "Passing Score Not Met",
    hi: "उत्तीर्ण अंक प्राप्त नहीं हुए",
  },
  "assess.viewCertificate": {
    en: "View Official Certificate",
    hi: "आधिकारिक प्रमाण पत्र देखें",
  },
  "assess.retake": { en: "Retake Assessment", hi: "पुनः परीक्षा दें" },

  // Certificates & Progress
  "cert.title": { en: "Certificate of Competency", hi: "दक्षता प्रमाण पत्र" },
  "cert.verified": {
    en: "Official Government Credential Verified",
    hi: "आधिकारिक सरकारी क्रेडेंशियल सत्यापित",
  },
  "cert.download": {
    en: "Print / Save PDF",
    hi: "प्रिंट / पीडीएफ सुरक्षित करें",
  },

  // Homepage - Hero
  "hero.title": {
    en: "National Learning Platform for Civil Services",
    hi: "सिविल सेवाओं हेतु राष्ट्रीय शिक्षण मंच",
  },
  "hero.subtitle": {
    en: "Integrated competency frameworks, accredited training modules, and verifiable certifications for India's administrative and statistical officers under Mission Karmayogi.",
    hi: "मिशन कर्मयोगी के अंतर्गत भारत के प्रशासनिक एवं सांख्यिकीय अधिकारियों हेतु एकीकृत क्षमता ढांचा, मान्यता प्राप्त प्रशिक्षण मॉड्यूल एवं सत्यापन योग्य प्रमाणन।",
  },
  "hero.signIn": {
    en: "Official Sign In",
    hi: "आधिकारिक लॉगिन",
  },
  "hero.explore": {
    en: "Explore Catalog",
    hi: "पाठ्यक्रम सूची देखें",
  },
  "hero.badgeMospi": {
    en: "MoSPI Accredited",
    hi: "एमओएसपीआई मान्यता प्राप्त",
  },
  "hero.badgeCbc": {
    en: "CBC Competency Framework",
    hi: "सीबीसी क्षमता ढांचा",
  },
  "hero.badgeIso": {
    en: "ISO/IEC Aligned",
    hi: "आईएसओ/आईईसी मानक",
  },
  "hero.slide1": {
    en: "Mission Karmayogi National Capacity Building",
    hi: "मिशन कर्मयोगी राष्ट्रीय क्षमता निर्माण",
  },
  "hero.slide2": {
    en: "Administrative Cadre Review & Policy Integration",
    hi: "प्रशासनिक संवर्ग समीक्षा एवं नीति समन्वय",
  },
  "hero.slide3": {
    en: "AI-Daksh Official Statistical & Analytical Tools",
    hi: "एआई-दक्ष आधिकारिक सांख्यिकी एवं विश्लेषणात्मक उपकरण",
  },

  // Homepage - Statistics
  "stats.trainedCount": { en: "40,000+", hi: "४०,०००+" },
  "stats.trainedLabel": {
    en: "Civil Servants Trained",
    hi: "प्रशिक्षित सिविल सेवक",
  },
  "stats.trainedSub": {
    en: "Central ministries & state cadres",
    hi: "केंद्रीय मंत्रालय एवं राज्य संवर्ग",
  },
  "stats.modulesCount": { en: "100%", hi: "१००%" },
  "stats.modulesLabel": {
    en: "Accredited Modules",
    hi: "मान्यता प्राप्त मॉड्यूल",
  },
  "stats.modulesSub": {
    en: "CBC certified curriculum standards",
    hi: "सीबीसी प्रमाणित पाठ्यक्रम मानक",
  },
  "stats.qualityCount": { en: "UN-NQAF", hi: "यूएन-एनक्यूएएफ" },
  "stats.qualityLabel": { en: "Quality Assurance", hi: "गुणवत्ता आश्वासन" },
  "stats.qualitySub": {
    en: "United Nations statistical rubrics",
    hi: "संयुक्त राष्ट्र सांख्यिकी मानक",
  },
  "stats.certCount": { en: "Verifiable", hi: "सत्यापन योग्य" },
  "stats.certLabel": { en: "Digital Credentials", hi: "डिजिटल क्रेडेंशियल" },
  "stats.certSub": {
    en: "Tamper-proof certificate hashes",
    hi: "छेड़छाड़-मुक्त प्रमाणपत्र डिजिटल हैश",
  },

  // Homepage - About
  "about.cardOrg": {
    en: "Mission Karmayogi (MoSPI)",
    hi: "मिशन कर्मयोगी (एमओएसपीआई)",
  },
  "about.cardSub": {
    en: "Capacity Building Commission",
    hi: "क्षमता निर्माण आयोग",
  },
  "about.item1Title": {
    en: "Official Statistical Cadre",
    hi: "आधिकारिक सांख्यिकी संवर्ग",
  },
  "about.item1Desc": {
    en: "Standardized NSS sample surveys, CPI price indices, and National Accounts compilation.",
    hi: "मानकीकृत एनएसएस नमूना सर्वेक्षण, सीपीआई मूल्य सूचकांक एवं राष्ट्रीय लेखा संकलन।",
  },
  "about.item2Title": {
    en: "Accredited 70% Threshold",
    hi: "मान्यता प्राप्त ७०% उत्तीर्ण सीमा",
  },
  "about.item2Desc": {
    en: "Verified assessments awarding official digital credentials recognized in service records.",
    hi: "सत्यापित मूल्यांकन जो सेवा अभिलेखों में मान्य आधिकारिक डिजिटल क्रेडेंशियल प्रदान करते हैं।",
  },
  "about.item3Title": {
    en: "Cadre Intelligence & AI",
    hi: "संवर्ग आसूचना एवं एआई",
  },
  "about.item3Desc": {
    en: "Automated guidance on departmental circulars, survey protocols, and field definitions.",
    hi: "विभागीय परिपत्रों, सर्वेक्षण प्रोटोकॉल और क्षेत्रीय परिभाषाओं पर त्वरित स्वचालित मार्गदर्शन।",
  },
  "about.title": {
    en: "A Competency-Driven Learning Paradigm",
    hi: "क्षमता-आधारित शिक्षण प्रतिमान",
  },
  "about.desc": {
    en: "Transitioning India's civil service from traditional procedural rules to dynamic, role-based competency mastery—aligned with the National Programme for Civil Services Capacity Building (NPCSCB).",
    hi: "भारतीय सिविल सेवा को पारंपरिक प्रक्रियात्मक नियमों से गतिशील, भूमिका-आधारित क्षमता दक्षता की ओर अग्रसर करना—राष्ट्रीय सिविल सेवा क्षमता निर्माण कार्यक्रम (एनपीसीएससीबी) के अनुरूप।",
  },
  "about.pillar1Title": {
    en: "Statistical Integrity & Methodologies",
    hi: "सांख्यिकीय सत्यनिष्ठा एवं कार्यप्रणाली",
  },
  "about.pillar1Desc": {
    en: "Curricula on National Sample Surveys (NSS), Consumer Price Index (CPI), IIP, and National Accounts compilation routines.",
    hi: "राष्ट्रीय नमूना सर्वेक्षण (एनएसएस), उपभोक्ता मूल्य सूचकांक (सीपीआई), आईआईपी और राष्ट्रीय लेखा संकलन विधियों पर विस्तृत पाठ्यक्रम।",
  },
  "about.pillar2Title": {
    en: "Certified Standardized Assessments",
    hi: "प्रमाणित मानकीकृत मूल्यांकन",
  },
  "about.pillar2Desc": {
    en: "Evaluations with a strict 70% passing threshold, awarding verifiable digital credentials linked to personnel service records.",
    hi: "कड़े ७०% उत्तीर्ण मानक वाले मूल्यांकन, जो कार्मिक सेवा अभिलेखों से जुड़े सत्यापन योग्य डिजिटल क्रेडेंशियल प्रदान करते हैं।",
  },
  "about.pillar3Title": {
    en: "AI-Orchestrated Cadre Assistant",
    hi: "एआई-संचालित संवर्ग सहायक",
  },
  "about.pillar3Desc": {
    en: "Built-in civil service assistant offering immediate guidance on survey methodologies, regulatory circulars, and course queries.",
    hi: "सर्वेक्षण कार्यप्रणाली, विनियामक परिपत्रों एवं पाठ्यक्रम प्रश्नों पर तत्काल मार्गदर्शन प्रदान करने वाला इन-बिल्ट सिविल सेवा सहायक।",
  },

  // Homepage - How It Works
  "howItWorks.title": {
    en: "How the Karmayogi Journey Works",
    hi: "कर्मयोगी शिक्षण यात्रा कैसे कार्य करती है",
  },
  "howItWorks.subtitle": {
    en: "A structured four-step path from cadre onboarding to recognized national civil service certification.",
    hi: "संवर्ग ऑनबोर्डिंग से लेकर मान्यता प्राप्त राष्ट्रीय सिविल सेवा प्रमाणन तक एक संरचित चार-चरणीय मार्ग।",
  },
  "howItWorks.step1Title": { en: "Onboard Role", hi: "भूमिका ऑनबोर्डिंग" },
  "howItWorks.step1Desc": {
    en: "Authenticate with official government email and specify your ministry and cadre domain.",
    hi: "आधिकारिक सरकारी ईमेल से प्रमाणीकरण करें और अपने मंत्रालय तथा संवर्ग कार्यक्षेत्र का चयन करें।",
  },
  "howItWorks.step2Title": {
    en: "Discover & Study",
    hi: "खोजें एवं अध्ययन करें",
  },
  "howItWorks.step2Desc": {
    en: "Study accredited video modules, CAPI survey simulations, and field methodology handbooks.",
    hi: "मान्यता प्राप्त वीडियो मॉड्यूल, सीएपीआई सर्वेक्षण सिमुलेशन और क्षेत्रीय कार्यप्रणाली पुस्तिकाओं का अध्ययन करें।",
  },
  "howItWorks.step3Title": {
    en: "Pass Assessment",
    hi: "मूल्यांकन उत्तीर्ण करें",
  },
  "howItWorks.step3Desc": {
    en: "Complete 70% threshold examinations with automated scoring and detailed question reviews.",
    hi: "स्वचालित मूल्यांकन और विस्तृत प्रश्न समीक्षा के साथ ७०% उत्तीर्ण सीमा वाली परीक्षाएं पूर्ण करें।",
  },
  "howItWorks.step4Title": {
    en: "Earn Certificate",
    hi: "प्रमाणपत्र प्राप्त करें",
  },
  "howItWorks.step4Desc": {
    en: "Receive cryptographically verifiable credentials linked to your official civil service record.",
    hi: "अपने आधिकारिक सिविल सेवा रिकॉर्ड से जुड़े क्रिप्टोग्राफिक रूप से सत्यापन योग्य क्रेडेंशियल प्राप्त करें।",
  },

  // Homepage - Resources
  "resources.title": {
    en: "Cadre Resources & Statistical Library",
    hi: "संवर्ग संसाधन एवं सांख्यिकी पुस्तकालय",
  },
  "resources.subtitle": {
    en: "Official survey manuals, quality frameworks, and technical reference handbooks curated by MoSPI, CSO, and NSSO.",
    hi: "सांख्यिकी मंत्रालय (MoSPI), सीएसओ और एनएसएसओ द्वारा तैयार आधिकारिक सर्वेक्षण नियमावलियां, गुणवत्ता रूपरेखाएं एवं संदर्भ पुस्तिकाएं।",
  },
  "resources.browseCatalog": {
    en: "Browse Full Catalog",
    hi: "संपूर्ण सूची देखें",
  },
  "resources.access": { en: "Access", hi: "देखें" },
  "resources.doc1Tag": { en: "NSSO Guide", hi: "एनएसएसओ मार्गदर्शिका" },
  "resources.doc1Title": {
    en: "Field Enumerator Manual",
    hi: "क्षेत्रीय प्रगणक नियमावली",
  },
  "resources.doc1Desc": {
    en: "Concepts, household sampling frameworks, and standardized definitions for socio-economic survey rounds.",
    hi: "सामाजिक-आर्थिक सर्वेक्षण दौर हेतु संकल्पनाएं, घरेलू नमूना चयन ढांचा और मानकीकृत परिभाषाएं।",
  },
  "resources.doc2Tag": { en: "Price Statistics", hi: "मूल्य सांख्यिकी" },
  "resources.doc2Title": {
    en: "CPI & IIP Technical Manual",
    hi: "सीपीआई एवं आईआईपी तकनीकी नियमावली",
  },
  "resources.doc2Desc": {
    en: "Retail price collection routines, item basket weighting diagrams, and index compilation methodologies.",
    hi: "खुदरा मूल्य संग्रह विधियां, वस्तु टोकरी भार आरेख और सूचकांक संकलन कार्यप्रणाली।",
  },
  "resources.doc3Tag": { en: "Quality Standards", hi: "गुणवत्ता मानक" },
  "resources.doc3Title": {
    en: "UN-NQAF Quality Rubrics",
    hi: "यूएन-एनक्यूएएफ गुणवत्ता रूपरेखा",
  },
  "resources.doc3Desc": {
    en: "United Nations National Quality Assurance Framework guidelines adapted for Indian official statistics.",
    hi: "भारतीय आधिकारिक सांख्यिकी हेतु अनुकूलित संयुक्त राष्ट्र राष्ट्रीय गुणवत्ता आश्वासन ढांचा दिशानिर्देश।",
  },
  "resources.doc4Tag": { en: "Survey Tech", hi: "सर्वेक्षण तकनीक" },
  "resources.doc4Title": {
    en: "CAPI Operations Manual",
    hi: "सीएपीआई संचालन नियमावली",
  },
  "resources.doc4Desc": {
    en: "Tablet-based interview setup, encrypted geo-tag synchronization, and automated logic validation procedures.",
    hi: "टैबलेट-आधारित साक्षात्कार सेटअप, एन्क्रिप्टेड भू-टैग सिंक्रनाइज़ेशन और स्वचालित सत्यापन प्रक्रियाएं।",
  },

  // Homepage - Help & Support
  "help.title": {
    en: "Help & Official Training Support",
    hi: "सहायता एवं आधिकारिक प्रशिक्षण केंद्र",
  },
  "help.subtitle": {
    en: "Official support channels for central civil servants, state statisticians, and ministry nodal officers.",
    hi: "केंद्रीय सिविल सेवकों, राज्य सांख्यिकीविदों और मंत्रालय के नोडल अधिकारियों हेतु आधिकारिक सहायता चैनल।",
  },
  "help.aiTitle": {
    en: "24/7 Civil Service AI Assistant",
    hi: "२४/७ सिविल सेवा एआई सहायक",
  },
  "help.aiDesc": {
    en: "Immediate, cited answers from official training manuals, survey sampling protocols, and circular guidelines.",
    hi: "आधिकारिक प्रशिक्षण नियमावलियों, सर्वेक्षण प्रोटोकॉल और परिपत्रों से तत्काल प्रामाणिक उत्तर प्राप्त करें।",
  },
  "help.aiLaunch": { en: "Launch AI Assistant", hi: "एआई सहायक प्रारंभ करें" },
  "help.deskTitle": {
    en: "Ministry Training Desk",
    hi: "मंत्रालय प्रशिक्षण सहायता केंद्र",
  },
  "help.deskDesc": {
    en: "For cadre verification, department approvals, or official nomination queries, reach out to the Central Training Division.",
    hi: "संवर्ग सत्यापन, विभागीय अनुमोदन या आधिकारिक नामांकन हेतु केंद्रीय प्रशिक्षण प्रभाग से संपर्क करें।",
  },
  "help.hours": {
    en: "Mon – Fri, 09:30 – 18:00 IST",
    hi: "सोम – शुक्र, ०९:३० – १८:०० आईएसटी",
  },
  "help.faqTitle": {
    en: "Frequently Asked Questions",
    hi: "अक्सर पूछे जाने वाले प्रश्न",
  },
  "help.faq1Q": {
    en: "How do I verify certificates?",
    hi: "प्रमाणपत्रों का सत्यापन कैसे करें?",
  },
  "help.faq1A": {
    en: "Every certificate includes a verifiable SHA-256 hash at /certificates.",
    hi: "प्रत्येक प्रमाणपत्र में /certificates पर सत्यापित करने योग्य एक SHA-256 हैश शामिल होता है।",
  },
  "help.faq2Q": {
    en: "What is the module pass threshold?",
    hi: "मॉड्यूल उत्तीर्ण करने की न्यूनतम सीमा क्या है?",
  },
  "help.faq2A": {
    en: "MoSPI accredited certifications require a 70% passing score on final evaluations.",
    hi: "एमओएसपीआई मान्यता प्राप्त प्रमाणन हेतु अंतिम मूल्यांकन में ७०% अंक आवश्यक हैं।",
  },
  "help.knowledgeBase": { en: "Knowledge Base", hi: "ज्ञान कोष" },

  // Homepage - Closing Banner
  "cta.readyTitle": {
    en: "Ready to advance your official competencies?",
    hi: "अपनी आधिकारिक क्षमताओं को सशक्त बनाने के लिए तैयार हैं?",
  },
  "cta.readyDesc": {
    en: "Sign in with your official government credentials or register with your nodal department officer today.",
    hi: "अपने आधिकारिक सरकारी क्रेडेंशियल से साइन इन करें या आज ही अपने नोडल विभाग अधिकारी से संपर्क कर पंजीकरण करें।",
  },
  "cta.register": { en: "Register New Official", hi: "नया अधिकारी पंजीकरण" },
  "cta.copyright": {
    en: "© 2026 iGOT Karmayogi Bharat • Capacity Building Commission • Ministry of Statistics & Programme Implementation",
    hi: "© २०२६ आईगॉट कर्मयोगी भारत • क्षमता निर्माण आयोग • सांख्यिकी एवं कार्यक्रम कार्यान्वयन मंत्रालय",
  },
  "cta.privacy": { en: "Privacy Policy", hi: "गोपनीयता नीति" },
  "cta.terms": { en: "Terms of Service", hi: "सेवा की शर्तें" },
  "cta.dataGov": { en: "Data Governance", hi: "डेटा प्रशासन" },
  "cta.helpdesk": { en: "Helpdesk", hi: "सहायता केंद्र" },
};

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType>({
  language: "en",
  setLanguage: () => {},
  t: (key: string) => key,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    const saved = localStorage.getItem("karmayogi_lang") as Language;
    if (saved && (saved === "en" || saved === "hi")) {
      setLanguageState(saved);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem("karmayogi_lang", lang);
  };

  const t = (key: string): string => {
    const entry = translations[key];
    if (!entry) return key;
    return entry[language] || entry.en || key;
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
